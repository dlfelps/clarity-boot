"""Aggregates per-scenario coverage + static analysis into report data."""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Set

from .static_analyzer import StaticAnalyzer

# Type alias for raw coverage data produced by TestRunner.
CoverageMap = Dict[str, List[int]]           # {rel_filepath: [lines]}
AllCoverage = Dict[str, CoverageMap]         # {scenario_name: CoverageMap}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class ScenarioMetrics:
    name: str
    loc: int                        # Total covered lines
    cyclomatic_complexity: float    # Sum of CC of covered functions
    unique_loc: int                 # Lines covered only by this scenario in feature
    is_hotspot: bool = False


@dataclass
class FeatureMetrics:
    name: str
    total_scenarios: int
    total_loc: int                  # Union of covered lines across all scenarios
    overall_cc: float               # Mean CC across scenarios
    component_dependencies: List[str]   # Unique source files touched
    scenarios: List[ScenarioMetrics] = field(default_factory=list)


@dataclass
class ComplexityReportData:
    project_name: str
    features: List[FeatureMetrics] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class AnalysisEngine:
    """Computes complexity metrics from raw coverage data."""

    def __init__(self, static_analyzer: StaticAnalyzer) -> None:
        self._analyzer = static_analyzer

    def analyze(
        self,
        project_dir: str,
        coverage_data: AllCoverage,
        parsed_features: List[dict],
    ) -> ComplexityReportData:
        """Build a ComplexityReportData object.

        Args:
            project_dir: Root of the target project (for resolving file paths).
            coverage_data: {scenario_name: {rel_filepath: [lines]}}
            parsed_features: [{"name": str, "scenarios": [{"name": str}]}]
        """
        project_name = os.path.basename(os.path.abspath(project_dir))
        feature_list: List[FeatureMetrics] = []

        for feature in parsed_features:
            feature_name = feature["name"]
            scenario_names = [s["name"] for s in feature["scenarios"]]

            # --- per-scenario pass ---
            scenario_metrics: List[ScenarioMetrics] = []
            for sname in scenario_names:
                scov = coverage_data.get(sname, {})
                loc = sum(len(lines) for lines in scov.values())
                cc = self._scenario_cc(project_dir, scov)
                unique = self._unique_loc(sname, scov, coverage_data, scenario_names)
                scenario_metrics.append(
                    ScenarioMetrics(name=sname, loc=loc,
                                    cyclomatic_complexity=cc, unique_loc=unique)
                )

            # --- feature-level aggregates ---
            if scenario_metrics:
                union_cov = self._union(
                    [coverage_data.get(n, {}) for n in scenario_names]
                )
                total_loc = sum(len(lines) for lines in union_cov.values())
                overall_cc = (
                    sum(s.cyclomatic_complexity for s in scenario_metrics)
                    / len(scenario_metrics)
                )
                deps = sorted({
                    fp
                    for n in scenario_names
                    for fp in coverage_data.get(n, {}).keys()
                })
            else:
                total_loc = 0
                overall_cc = 0.0
                deps = []

            # --- hotspot detection: CC >= 2× feature average ---
            for sm in scenario_metrics:
                if overall_cc > 0 and sm.cyclomatic_complexity >= 2 * overall_cc:
                    sm.is_hotspot = True

            feature_list.append(FeatureMetrics(
                name=feature_name,
                total_scenarios=len(scenario_metrics),
                total_loc=total_loc,
                overall_cc=round(overall_cc, 2),
                component_dependencies=deps,
                scenarios=scenario_metrics,
            ))

        return ComplexityReportData(project_name=project_name, features=feature_list)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _scenario_cc(self, project_dir: str, scov: CoverageMap) -> float:
        """Sum cyclomatic complexity of all functions exercised by the scenario."""
        total = 0.0
        for rel_path, lines in scov.items():
            full_path = os.path.join(project_dir, rel_path)
            if os.path.exists(full_path):
                _, cc = self._analyzer.calculate_complexity(full_path, lines)
                total += cc
        return round(total, 2)

    def _unique_loc(
        self,
        scenario_name: str,
        scov: CoverageMap,
        all_coverage: AllCoverage,
        feature_scenario_names: List[str],
    ) -> int:
        """Count lines covered by this scenario and no other scenario in the feature."""
        unique_total = 0
        for filepath, lines in scov.items():
            our: Set[int] = set(lines)
            others: Set[int] = set()
            for other in feature_scenario_names:
                if other == scenario_name:
                    continue
                others |= set(all_coverage.get(other, {}).get(filepath, []))
            unique_total += len(our - others)
        return unique_total

    def _union(self, coverage_list: List[CoverageMap]) -> Dict[str, Set[int]]:
        """Union multiple CoverageMap dicts into one."""
        result: Dict[str, Set[int]] = {}
        for cov in coverage_list:
            for fp, lines in cov.items():
                result.setdefault(fp, set()).update(lines)
        return result
