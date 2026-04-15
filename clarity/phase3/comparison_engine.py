"""Load two Phase 2 data.json files and build a side-by-side ComparisonReportData."""

import json
import os
from dataclasses import dataclass, field
from typing import List

from ..phase2.analysis_engine import ComplexityReportData, FeatureMetrics, ScenarioMetrics


# ---------------------------------------------------------------------------
# Deserialisation helpers
# ---------------------------------------------------------------------------

def _scenario_from_dict(d: dict) -> ScenarioMetrics:
    return ScenarioMetrics(
        name=d["name"],
        loc=d["loc"],
        cyclomatic_complexity=d["cyclomatic_complexity"],
        unique_loc=d["unique_loc"],
        is_hotspot=d.get("is_hotspot", False),
    )


def _feature_from_dict(d: dict) -> FeatureMetrics:
    return FeatureMetrics(
        name=d["name"],
        total_scenarios=d["total_scenarios"],
        total_loc=d["total_loc"],
        overall_cc=d["overall_cc"],
        component_dependencies=d.get("component_dependencies", []),
        scenarios=[_scenario_from_dict(s) for s in d.get("scenarios", [])],
    )


def load_report(report_dir: str) -> ComplexityReportData:
    """Load a Phase 2 data.json from *report_dir* into a ComplexityReportData.

    Raises:
        FileNotFoundError: if data.json is absent from *report_dir*.
    """
    json_path = os.path.join(report_dir, "data.json")
    if not os.path.exists(json_path):
        raise FileNotFoundError(
            f"No data.json found in report directory: {report_dir}"
        )
    with open(json_path, encoding="utf-8") as fh:
        raw = json.load(fh)
    return ComplexityReportData(
        project_name=raw["project_name"],
        features=[_feature_from_dict(f) for f in raw.get("features", [])],
    )


# ---------------------------------------------------------------------------
# Comparison data model
# ---------------------------------------------------------------------------

@dataclass
class ScenarioComparison:
    name: str
    loc_a: int
    loc_b: int
    loc_delta: int          # b − a  (positive = b is larger)
    cc_a: float
    cc_b: float
    cc_delta: float         # b − a
    unique_loc_a: int
    unique_loc_b: int
    is_hotspot_a: bool
    is_hotspot_b: bool


@dataclass
class FeatureComparison:
    name: str
    total_scenarios: int
    total_loc_a: int
    total_loc_b: int
    loc_delta: int
    overall_cc_a: float
    overall_cc_b: float
    cc_delta: float
    scenarios: List[ScenarioComparison] = field(default_factory=list)


@dataclass
class ComparisonReportData:
    project_name_a: str
    project_name_b: str
    features: List[FeatureComparison] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Comparison builder
# ---------------------------------------------------------------------------

def build_comparison(report_a: ComplexityReportData,
                     report_b: ComplexityReportData) -> ComparisonReportData:
    """Align two ComplexityReportData objects by feature/scenario name.

    Raises:
        ValueError: if the feature/scenario names do not match exactly.
    """
    names_a = sorted(f.name for f in report_a.features)
    names_b = sorted(f.name for f in report_b.features)
    if names_a != names_b:
        only_a = set(names_a) - set(names_b)
        only_b = set(names_b) - set(names_a)
        parts = []
        if only_a:
            parts.append(f"only in report A: {sorted(only_a)}")
        if only_b:
            parts.append(f"only in report B: {sorted(only_b)}")
        raise ValueError(
            "Reports have different feature sets — cannot compare. "
            + "; ".join(parts)
        )

    feature_map_b = {f.name: f for f in report_b.features}
    comparisons: List[FeatureComparison] = []

    for fa in report_a.features:
        fb = feature_map_b[fa.name]

        # Validate matching scenario names within the feature.
        snames_a = sorted(s.name for s in fa.scenarios)
        snames_b = sorted(s.name for s in fb.scenarios)
        if snames_a != snames_b:
            only_sa = set(snames_a) - set(snames_b)
            only_sb = set(snames_b) - set(snames_a)
            parts = []
            if only_sa:
                parts.append(f"only in A: {sorted(only_sa)}")
            if only_sb:
                parts.append(f"only in B: {sorted(only_sb)}")
            raise ValueError(
                f"Feature '{fa.name}' has different scenario sets — cannot compare. "
                + "; ".join(parts)
            )

        smap_b = {s.name: s for s in fb.scenarios}
        scenario_comparisons: List[ScenarioComparison] = []
        for sa in fa.scenarios:
            sb = smap_b[sa.name]
            scenario_comparisons.append(ScenarioComparison(
                name=sa.name,
                loc_a=sa.loc,
                loc_b=sb.loc,
                loc_delta=sb.loc - sa.loc,
                cc_a=sa.cyclomatic_complexity,
                cc_b=sb.cyclomatic_complexity,
                cc_delta=round(sb.cyclomatic_complexity - sa.cyclomatic_complexity, 2),
                unique_loc_a=sa.unique_loc,
                unique_loc_b=sb.unique_loc,
                is_hotspot_a=sa.is_hotspot,
                is_hotspot_b=sb.is_hotspot,
            ))

        comparisons.append(FeatureComparison(
            name=fa.name,
            total_scenarios=fa.total_scenarios,
            total_loc_a=fa.total_loc,
            total_loc_b=fb.total_loc,
            loc_delta=fb.total_loc - fa.total_loc,
            overall_cc_a=fa.overall_cc,
            overall_cc_b=fb.overall_cc,
            cc_delta=round(fb.overall_cc - fa.overall_cc, 2),
            scenarios=scenario_comparisons,
        ))

    return ComparisonReportData(
        project_name_a=report_a.project_name,
        project_name_b=report_b.project_name,
        features=comparisons,
    )
