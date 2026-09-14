"""
Phase 8 - Design validator.

Rule-based pass/fail/warning checks that decide whether the simulated
passive-shelter design actually behaves the way a good passive design
should for its climate zone, and whether the ANSYS run agrees closely
enough with the independent simplified model to be trusted.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum

from config import ClimateZone, SimulationSettings
from core.metrics_extractor import ThermalMetrics
from core.comparator import ComparisonReport


class Verdict(str, Enum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


@dataclass
class ValidationRuleResult:
    rule: str
    verdict: Verdict
    detail: str

    def to_dict(self) -> dict:
        d = asdict(self)
        d["verdict"] = self.verdict.value
        return d


@dataclass
class ValidationReport:
    rules: list
    overall_verdict: Verdict

    def to_dict(self) -> dict:
        return {
            "rules": [r.to_dict() for r in self.rules],
            "overall_verdict": self.overall_verdict.value,
        }


# Minimum expected decrement factor ceiling per climate zone: a well
# designed passive shelter should damp the outdoor swing significantly.
_MAX_DECREMENT_FACTOR = {
    ClimateZone.HOT_DRY: 0.65,
    ClimateZone.WARM_HUMID: 0.75,
    ClimateZone.COMPOSITE: 0.70,
    ClimateZone.TEMPERATE: 0.85,
    ClimateZone.COLD: 0.90,
}

_MIN_THERMAL_LAG_HOURS = {
    ClimateZone.HOT_DRY: 4.0,
    ClimateZone.WARM_HUMID: 2.0,
    ClimateZone.COMPOSITE: 3.0,
    ClimateZone.TEMPERATE: 1.5,
    ClimateZone.COLD: 1.0,
}


def validate(ansys_metrics: ThermalMetrics,
             comparison: ComparisonReport,
             climate_zone: ClimateZone,
             settings: SimulationSettings) -> ValidationReport:

    rules = []

    # Rule 1: decrement factor within expectation for the climate zone
    max_df = _MAX_DECREMENT_FACTOR.get(climate_zone, 0.8)
    if ansys_metrics.decrement_factor <= max_df:
        rules.append(ValidationRuleResult(
            "decrement_factor_within_climate_expectation", Verdict.PASS,
            f"Decrement factor {ansys_metrics.decrement_factor} <= expected max {max_df} "
            f"for {climate_zone.value}."))
    elif ansys_metrics.decrement_factor <= max_df * 1.15:
        rules.append(ValidationRuleResult(
            "decrement_factor_within_climate_expectation", Verdict.WARNING,
            f"Decrement factor {ansys_metrics.decrement_factor} slightly exceeds "
            f"expected max {max_df} for {climate_zone.value}."))
    else:
        rules.append(ValidationRuleResult(
            "decrement_factor_within_climate_expectation", Verdict.FAIL,
            f"Decrement factor {ansys_metrics.decrement_factor} exceeds expected max "
            f"{max_df} for {climate_zone.value} -- envelope is not damping outdoor "
            "swings adequately; consider more thermal mass or insulation."))

    # Rule 2: thermal lag meets minimum for passive strategy to be useful
    min_lag = _MIN_THERMAL_LAG_HOURS.get(climate_zone, 2.0)
    if ansys_metrics.thermal_lag_hours >= min_lag:
        rules.append(ValidationRuleResult(
            "thermal_lag_sufficient", Verdict.PASS,
            f"Thermal lag {ansys_metrics.thermal_lag_hours}h >= minimum {min_lag}h."))
    else:
        rules.append(ValidationRuleResult(
            "thermal_lag_sufficient", Verdict.WARNING,
            f"Thermal lag {ansys_metrics.thermal_lag_hours}h is below the {min_lag}h "
            "usually needed to push peak indoor heat into unoccupied hours."))

    # Rule 3: comfort hours
    if ansys_metrics.comfort_pct >= 70:
        rules.append(ValidationRuleResult(
            "comfort_band_coverage", Verdict.PASS,
            f"{ansys_metrics.comfort_pct}% of the day stays within the comfort band."))
    elif ansys_metrics.comfort_pct >= 50:
        rules.append(ValidationRuleResult(
            "comfort_band_coverage", Verdict.WARNING,
            f"Only {ansys_metrics.comfort_pct}% of the day is within the comfort band."))
    else:
        rules.append(ValidationRuleResult(
            "comfort_band_coverage", Verdict.FAIL,
            f"Just {ansys_metrics.comfort_pct}% of the day is within the comfort band -- "
            "design likely needs additional passive interventions."))

    # Rule 4: ANSYS vs simplified-model agreement (trust check)
    if comparison.overall_within_tolerance:
        rules.append(ValidationRuleResult(
            "ansys_simplified_agreement", Verdict.PASS,
            f"All tracked metrics agree within {settings.deviation_tolerance_pct}% "
            f"tolerance (indoor-temp RMSE {comparison.rmse_indoor_temp_c} C, "
            f"correlation {comparison.correlation_indoor_temp})."))
    else:
        worst = max(comparison.metric_comparisons, key=lambda c: c.pct_diff)
        rules.append(ValidationRuleResult(
            "ansys_simplified_agreement", Verdict.WARNING,
            f"Largest deviation is on '{worst.metric}' at {worst.pct_diff}% "
            f"(tolerance {settings.deviation_tolerance_pct}%). Investigate model "
            "assumptions (thermal mass class, envelope areas) before trusting results."))

    # Overall verdict = worst individual verdict
    if any(r.verdict == Verdict.FAIL for r in rules):
        overall = Verdict.FAIL
    elif any(r.verdict == Verdict.WARNING for r in rules):
        overall = Verdict.WARNING
    else:
        overall = Verdict.PASS

    return ValidationReport(rules=rules, overall_verdict=overall)
