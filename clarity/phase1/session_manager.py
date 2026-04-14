"""Stateful interactive session for Phase 1 Gherkin spec generation."""

import os
from pathlib import Path
import click

from .feature_agent import FeatureAgent


class InteractiveSessionManager:
    """Manages the user-facing loop for drafting and approving a Gherkin spec."""

    def __init__(self) -> None:
        # Agent is created lazily, after prompt validation, so that an empty
        # prompt is rejected before the API key is ever checked.
        self.agent: FeatureAgent | None = None
        self.current_prompt: str = ""
        self.gherkin_draft: str = ""
        self.feedback_log: list[str] = []

    def run(
        self,
        feature_name: str | None = None,
        output_path: str | None = None,
        model: str = "claude-sonnet-4-6",
    ) -> None:
        """Start the interactive session.

        Loops until the user types 'approve', then writes the spec to output_path.

        Args:
            feature_name: Short name for the feature (e.g. "user_auth"). Used to
                derive the output path as specs/<feature_name>.feature when
                output_path is not given explicitly.
            output_path: Explicit destination path. Overrides feature_name-derived
                path. Kept for backward compatibility.
            model: Anthropic model identifier to use for generation.

        Raises:
            click.ClickException: if the initial prompt is empty.
        """
        click.echo("=" * 62)
        click.echo("  Clarity Engine — Phase 1: Interactive Spec Generation")
        click.echo("=" * 62)
        click.echo()

        # Allow empty input so we can validate it ourselves (click.prompt
        # default="" prevents re-prompting on empty strings).
        self.current_prompt = click.prompt(
            "Describe your project or feature",
            default="",
            show_default=False,
            prompt_suffix="\n> ",
        ).strip()

        if not self.current_prompt:
            raise click.ClickException("Prompt cannot be empty.")

        # Resolve output path.
        if output_path is None:
            if feature_name is None:
                feature_name = click.prompt(
                    "Feature name (used as filename in specs/)",
                    prompt_suffix="\n> ",
                ).strip()
            output_path = os.path.join("specs", f"{feature_name}.feature")

        # Load existing spec if one is already saved at the resolved path.
        existing_draft = ""
        if os.path.exists(output_path):
            existing_draft = Path(output_path).read_text(encoding="utf-8").strip()
            if existing_draft:
                click.echo(
                    f"\nFound existing spec at {output_path!r} — loading for refinement.\n"
                )
                click.echo("-" * 62)
                click.echo(existing_draft)
                click.echo("-" * 62)

        # Validate API key only after we know the prompt is non-empty.
        self.agent = FeatureAgent(model=model)

        if existing_draft:
            self.gherkin_draft = existing_draft
            questions: list[str] = []
        else:
            click.echo("\nGenerating Gherkin specification…\n")
            click.echo("-" * 62)
            self.gherkin_draft, questions = self.agent.generate_gherkin(
                self.current_prompt
            )
            # Always display the draft after generation (the streaming agent already
            # prints tokens live, but echoing here ensures tests and non-streaming
            # paths always show the result).
            click.echo(self.gherkin_draft)
            click.echo("-" * 62)

        while True:
            click.echo("\n" + "=" * 62)
            if questions:
                click.echo("\nClarifying questions:")
                for i, q in enumerate(questions, 1):
                    click.echo(f"  {i}. {q}")
            click.echo()
            click.echo("Commands:")
            click.echo('  • Type feedback to refine the spec')
            click.echo('  • Type "show"    to display the current spec again')
            click.echo('  • Type "approve" to finalise and save')

            user_input = click.prompt(
                "\nYour input",
                default="",
                show_default=False,
                prompt_suffix="\n> ",
            ).strip()

            if not user_input:
                click.echo("Please provide feedback, or type 'approve'.")
                continue

            command = user_input.lower()

            if command == "approve":
                project_root = self._save(output_path)
                click.echo(
                    f"\n✓ Phase 1 complete. Specification saved to: {output_path}"
                )
                click.echo(f"\n  Project scaffold created at: {project_root}")
                click.echo("    src/                           — place application code here")
                click.echo("    features/steps/                — place behave step definitions here")
                click.echo("    IMPLEMENTATION_INSTRUCTIONS.md — guidance for the implementing agent")
                return

            if command == "show":
                click.echo("\nCurrent specification:")
                click.echo("-" * 62)
                click.echo(self.gherkin_draft)
                click.echo("-" * 62)
                continue

            # Treat anything else as refinement feedback
            self.feedback_log.append(user_input)
            click.echo("\nRefining specification…\n")
            click.echo("-" * 62)

            self.gherkin_draft, questions = self.agent.generate_gherkin(
                prompt=self.current_prompt,
                previous_gherkin=self.gherkin_draft,
                user_feedback=user_input,
            )
            click.echo(self.gherkin_draft)
            click.echo("-" * 62)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _save(self, output_path: str) -> Path:
        """Save the approved spec and scaffold the project structure.

        Returns:
            The project root directory that was scaffolded.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.gherkin_draft + "\n", encoding="utf-8")

        # Project root is two levels up when the spec lives in specs/, otherwise
        # treat the spec's parent directory as the root.
        project_root = path.parent.parent if path.parent.name == "specs" else path.parent
        self._setup_project(project_root)
        return project_root

    def _setup_project(self, project_root: Path) -> None:
        """Create the implementation scaffold expected by Phase 2."""
        (project_root / "src").mkdir(exist_ok=True)
        (project_root / "features" / "steps").mkdir(parents=True, exist_ok=True)

        dst = project_root / "IMPLEMENTATION_INSTRUCTIONS.md"
        if not dst.exists():
            src = Path(__file__).parent.parent / "data" / "IMPLEMENTATION_INSTRUCTIONS.md"
            if src.exists():
                dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
