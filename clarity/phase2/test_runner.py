"""Wrapper around behave + coverage.py for per-scenario coverage measurement."""

import os
import re
import sys
import subprocess
import tempfile
from typing import Dict, List

import coverage as coverage_module

# Per-scenario coverage: {relative_filepath: [covered_line_numbers]}
ScenarioCoverage = Dict[str, List[int]]


class TestRunner:
    """Runs a behave test suite and measures line coverage per scenario."""

    # Paths to exclude from source coverage (test infrastructure, etc.)
    _EXCLUDE_PATTERNS = (
        "features/",
        "steps/",
        ".tox/",
        "venv/",
        ".venv/",
        "site-packages/",
        "__pycache__/",
        "conftest.py",
        "setup.py",
        "setup.cfg",
    )

    def run_all_tests(self, project_dir: str) -> None:
        """Run the full behave test suite.

        Raises:
            ValueError: if any test fails or behave exits non-zero.
        """
        result = subprocess.run(
            [sys.executable, "-m", "behave", "features/", "--no-capture"],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise ValueError(
                "Cannot generate a report for a project with failing tests."
            )

    def run_scenario_with_coverage(
        self,
        project_dir: str,
        scenario_name: str,
        features_path: str = "features/",
    ) -> ScenarioCoverage:
        """Run a single scenario and return line-level coverage data.

        Args:
            project_dir: Absolute path to the target project root.
            scenario_name: Exact scenario name to run (matched as ^…$).
            features_path: Relative path to the features directory.

        Returns:
            Mapping from relative file path to sorted list of covered lines.
            Returns an empty dict if the scenario produced no coverage data.
        """
        # Unique temp file so parallel invocations don't collide.
        with tempfile.NamedTemporaryFile(
            suffix=".coverage", dir=project_dir, delete=False
        ) as tmp:
            coverage_file = tmp.name

        try:
            # Anchor the name as an exact regex match to avoid substring hits.
            pattern = f"^{re.escape(scenario_name)}$"

            subprocess.run(
                [
                    sys.executable, "-m", "coverage", "run",
                    f"--data-file={coverage_file}",
                    "--source", ".",
                    "-m", "behave",
                    features_path,
                    "--name", pattern,
                    "--no-capture",
                    "--quiet",
                    "--no-summary",
                ],
                cwd=project_dir,
                capture_output=True,
                text=True,
            )

            if not os.path.exists(coverage_file):
                return {}

            cov = coverage_module.Coverage(data_file=coverage_file)
            cov.load()
            data = cov.get_data()

            result: ScenarioCoverage = {}
            for filepath in data.measured_files():
                rel = os.path.relpath(filepath, project_dir).replace("\\", "/")
                if self._is_source_file(rel):
                    lines = data.lines(filepath)
                    if lines:
                        result[rel] = sorted(lines)

            return result

        finally:
            if os.path.exists(coverage_file):
                os.remove(coverage_file)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_source_file(self, rel_path: str) -> bool:
        """Return True only for application source files (not test infra)."""
        if not rel_path.endswith(".py"):
            return False
        return not any(pat in rel_path for pat in self._EXCLUDE_PATTERNS)
