"""Orchestrates the Phase 2 report pipeline."""

import os
from typing import List

import click

from .analysis_engine import AnalysisEngine
from .report_builder import ReportBuilder
from .static_analyzer import StaticAnalyzer
from .test_runner import TestRunner


def parse_gherkin(feature_file_path: str) -> List[dict]:
    """Parse a Gherkin file and return features with their scenarios.

    Returns:
        [{"name": str, "scenarios": [{"name": str}]}]
    """
    features: List[dict] = []
    current_feature: dict | None = None

    with open(feature_file_path, "r", encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if line.startswith("Feature:"):
                current_feature = {
                    "name": line[len("Feature:"):].strip(),
                    "scenarios": [],
                }
                features.append(current_feature)
            elif line.startswith("Scenario Outline:") and current_feature is not None:
                current_feature["scenarios"].append(
                    {"name": line[len("Scenario Outline:"):].strip()}
                )
            elif line.startswith("Scenario:") and current_feature is not None:
                current_feature["scenarios"].append(
                    {"name": line[len("Scenario:"):].strip()}
                )

    return features


class ReportManager:
    """Top-level orchestrator for the Phase 2 transparency report."""

    def __init__(self) -> None:
        self._runner = TestRunner()
        self._analyzer = StaticAnalyzer()
        self._engine = AnalysisEngine(self._analyzer)
        self._builder = ReportBuilder()

    def generate(self, project_dir: str, output_dir: str) -> str:
        """Run the full report pipeline.

        Args:
            project_dir: Path to the target project directory.
            output_dir: Directory where the report folder will be written.

        Returns:
            Absolute path to the generated report/index.html.

        Raises:
            click.ClickException: on validation failure or test failures.
        """
        project_dir = os.path.abspath(project_dir)
        output_dir = os.path.abspath(output_dir)

        # ── 1. Validate ──────────────────────────────────────────────
        self._validate(project_dir)

        approved = os.path.join(project_dir, "approved.feature")

        click.echo("Parsing approved.feature…")
        parsed = parse_gherkin(approved)
        if not parsed:
            raise click.ClickException(
                "No features found in approved.feature."
            )

        all_scenarios = [s["name"] for f in parsed for s in f["scenarios"]]
        click.echo(
            f"Found {len(parsed)} feature(s), {len(all_scenarios)} scenario(s)."
        )

        # ── 2. Confirm all tests pass ────────────────────────────────
        click.echo("Running test suite…")
        try:
            self._runner.run_all_tests(project_dir)
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        click.echo("✓ All tests passed.")

        # ── 3. Per-scenario coverage ─────────────────────────────────
        coverage_data: dict = {}
        for scenario in all_scenarios:
            click.echo(f"  Measuring coverage for: {scenario!r}…")
            coverage_data[scenario] = self._runner.run_scenario_with_coverage(
                project_dir, scenario
            )

        # ── 4. Complexity analysis ───────────────────────────────────
        click.echo("Analysing complexity…")
        report_data = self._engine.analyze(project_dir, coverage_data, parsed)

        # ── 5. Build report ──────────────────────────────────────────
        click.echo("Building report…")
        os.makedirs(output_dir, exist_ok=True)
        report_path = self._builder.build(report_data, output_dir)

        return report_path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _validate(self, project_dir: str) -> None:
        if not os.path.isdir(project_dir):
            raise click.ClickException(
                f"Project directory not found: {project_dir}"
            )

        if not os.path.exists(os.path.join(project_dir, "approved.feature")):
            raise click.ClickException(
                "Project is missing the required 'approved.feature' file."
            )

        if not os.path.isdir(os.path.join(project_dir, "features")):
            raise click.ClickException(
                "Project is missing a 'features/' directory with behave tests."
            )
