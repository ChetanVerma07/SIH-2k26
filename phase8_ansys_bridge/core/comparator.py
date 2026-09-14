"""
Phase 8 - ANSYS vs simplified-model comparator.

Compares two ThermalMetrics objects (one from the ANSYS/mock backend, one
from the independent simplified model) metric-by-metric, plus a
timeseries-level RMSE / correlation check on indoor temperature.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict

from core.metrics_extractor import ThermalMetrics
from core.results_importer import ThermalTimeSeries


@dataclass
class MetricComparison:
    metric: str
    ansys_value: float
    simplified_value: float
    abs_diff: float
    pct_diff: float
    within_tolerance: bool


@dataclass
class ComparisonReport:
    metric_comparisons: list
    rmse_indoor_temp_c: float
    correlation_indoor_temp: float
    overall_within_tolerance: bool

    def to_dict(self) -> dict:
        return {
            "metric_comparisons": [asdict(m) for m in self.metric_comparisons],
            "rmse_indoor_temp_c": self.rmse_indoor_temp_c,
            "correlation_indoor_temp": self.correlation_indoor_temp,
            "overall_within_tolerance": self.overall_within_tolerance,
        }


_COMPARE_FIELDS = [
    "peak_indoor_temp_c", "min_indoor_temp_c", "mean_indoor_temp_c",
    "indoor_temp_swing_c", "decrement_factor", "thermal_lag_hours",
    "comfort_hours", "peak_heat_flux_w_m2",
]


def _pct_diff(a: float, b: float) -> float:
    denom = abs(a) if abs(a) > 1e-6 else 1e-6
    return 100.0 * abs(a - b) / denom


def _rmse(a: list, b: list) -> float:
    n = min(len(a), len(b))
    if n == 0:
        return 0.0
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(n)) / n)


def _pearson_corr(a: list, b: list) -> float:
    n = min(len(a), len(b))
    if n < 2:
        return 0.0
    a, b = a[:n], b[:n]
    mean_a = sum(a) / n
    mean_b = sum(b) / n
    cov = sum((a[i] - mean_a) * (b[i] - mean_b) for i in range(n))
    var_a = sum((x - mean_a) ** 2 for x in a)
    var_b = sum((x - mean_b) ** 2 for x in b)
    denom = math.sqrt(var_a * var_b)
    return cov / denom if denom > 1e-9 else 0.0


def compare(ansys_metrics: ThermalMetrics, simplified_metrics: ThermalMetrics,
            ansys_series: ThermalTimeSeries, simplified_series: ThermalTimeSeries,
            tolerance_pct: float = 15.0) -> ComparisonReport:

    comparisons = []
    for field in _COMPARE_FIELDS:
        a_val = getattr(ansys_metrics, field)
        s_val = getattr(simplified_metrics, field)
        diff = abs(a_val - s_val)
        pct = _pct_diff(a_val, s_val)
        comparisons.append(MetricComparison(
            metric=field,
            ansys_value=a_val,
            simplified_value=s_val,
            abs_diff=round(diff, 3),
            pct_diff=round(pct, 2),
            within_tolerance=pct <= tolerance_pct,
        ))

    rmse = _rmse(ansys_series.indoor_temp_c, simplified_series.indoor_temp_c)
    corr = _pearson_corr(ansys_series.indoor_temp_c, simplified_series.indoor_temp_c)

    overall_ok = all(c.within_tolerance for c in comparisons) and rmse <= 2.0

    return ComparisonReport(
        metric_comparisons=comparisons,
        rmse_indoor_temp_c=round(rmse, 3),
        correlation_indoor_temp=round(corr, 3),
        overall_within_tolerance=overall_ok,
    )
