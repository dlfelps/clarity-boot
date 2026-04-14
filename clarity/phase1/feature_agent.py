"""LLM client for Gherkin spec generation using the Anthropic API."""

import os
from typing import Optional
import anthropic

SYSTEM_PROMPT = """You are an expert in Behavior-Driven Development (BDD) and Gherkin syntax.
Your role is to help software developers and product managers create precise,
human-readable Gherkin feature specifications.

When generating or refining Gherkin:
- Use proper Feature, Background, Scenario, Given/When/Then/And/But keywords
- Write clear, business-readable scenarios non-technical stakeholders can understand
- Cover the happy path first, then edge cases and error scenarios
- Use concrete examples with realistic data; use tables (Examples:) where appropriate
- Keep each scenario focused on a single behavior
- Avoid implementation details in scenario steps

Your response MUST always follow this exact format:
1. The complete Gherkin feature file (starting with "Feature:")
2. A separator line containing only: ---QUESTIONS---
3. Either 2-4 numbered clarifying questions, or the single word NONE

Example:
Feature: User Authentication
  As a registered user
  I want to log in to the system
  So that I can access my account

  Scenario: Successful login with valid credentials
    Given I am on the login page
    When I enter a valid email and password
    Then I am redirected to my dashboard

---QUESTIONS---
1. Should the system support a "Remember me" option to persist sessions?
2. What should happen after 5 consecutive failed login attempts?"""


class FeatureAgent:
    """Wraps the Anthropic API to generate and refine Gherkin specifications."""

    def __init__(self, model: str = "claude-sonnet-4-6") -> None:
        api_key = os.environ.get("CLAUDE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "CLAUDE_API_KEY environment variable is not set. "
                "Please export your Anthropic API key as CLAUDE_API_KEY."
            )
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def generate_gherkin(
        self,
        prompt: str,
        previous_gherkin: Optional[str] = None,
        user_feedback: Optional[str] = None,
    ) -> tuple[str, list[str]]:
        """Generate or refine a Gherkin specification.

        Args:
            prompt: The original project/feature description from the user.
            previous_gherkin: The current draft to refine (None for first generation).
            user_feedback: Plain-English feedback for the refinement pass.

        Returns:
            A (gherkin_text, questions) tuple. questions may be an empty list.
        """
        if previous_gherkin and user_feedback:
            user_content = (
                f"Original project description:\n{prompt}\n\n"
                f"Current Gherkin specification:\n```gherkin\n{previous_gherkin}\n```\n\n"
                f"User feedback: {user_feedback}\n\n"
                "Please update the Gherkin specification to incorporate the feedback."
            )
        else:
            user_content = (
                f"Generate a Gherkin feature specification for the following:\n\n{prompt}"
            )

        full_text = ""

        # System prompt is stable across turns — cache it.
        # Stream the response so the user sees Gherkin tokens as they arrive.
        with self.client.messages.stream(
            model=self.model,
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_content}],
        ) as stream:
            for text_chunk in stream.text_stream:
                full_text += text_chunk
                print(text_chunk, end="", flush=True)

        print()  # final newline after streaming

        return self._parse_response(full_text)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_response(self, raw: str) -> tuple[str, list[str]]:
        """Split the raw LLM response into (gherkin, questions)."""
        separator = "---QUESTIONS---"
        if separator in raw:
            gherkin_part, questions_part = raw.split(separator, 1)
            gherkin = gherkin_part.strip()
            questions = self._extract_questions(questions_part.strip())
        else:
            gherkin = raw.strip()
            questions = []

        return gherkin, questions

    def _extract_questions(self, text: str) -> list[str]:
        if not text or text.upper() == "NONE":
            return []
        questions = []
        for line in text.splitlines():
            line = line.strip()
            if line and line[0].isdigit():
                # Strip leading "1. " / "2) " etc.
                cleaned = line.lstrip("0123456789.)- ").strip()
                if cleaned:
                    questions.append(cleaned)
        return questions
