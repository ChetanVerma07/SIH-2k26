"""Recommendation engine.

Explains the selected design using its actual computed metrics. Never
invents numbers — every figure quoted here is read from the
ThermalPerformance / BaselineComparison / RobustnessSummary objects passed
in.
"""
from app.models.design import ShelterDesign
from app.models.results import (
    ThermalPerformance,
    BaselineComparison,
    RobustnessSummary,
    RecommendationExplanation,
)


def generate_recommendation(
    design: ShelterDesign,
    performance: ThermalPerformance,
    comparison: BaselineComparison,
    robustness: RobustnessSummary,
) -> RecommendationExplanation:
    headline = (
        f"{design.label} is recommended because it maintained "
        f"{performance.comfort_percentage:.0f}% of the simulation period within the target "
        f"comfort range and had {comparison.heat_loss_improvement_percent:.0f}% lower heat loss "
        f"than the baseline design."
    )

    reasons: list[str] = [
        f"Comfort coverage of {performance.comfort_percentage:.1f}% versus "
        f"{comparison.baseline_comfort_percentage:.1f}% for the baseline "
        f"({comparison.comfort_improvement_points:+.1f} percentage points).",
        f"Heat loss of {performance.total_heat_loss_kwh:.1f} kWh versus "
        f"{comparison.baseline_heat_loss_kwh:.1f} kWh for the baseline "
        f"({comparison.heat_loss_improvement_percent:.1f}% improvement).",
        f"Estimated auxiliary heating requirement of "
        f"{performance.estimated_heating_requirement_kwh:.1f} kWh versus "
        f"{comparison.baseline_heating_requirement_kwh:.1f} kWh for the baseline "
        f"({comparison.heating_requirement_improvement_percent:.1f}% improvement).",
        f"Robustness score of {robustness.robustness_score:.1f}/100 across "
        f"{robustness.scenarios_evaluated} alternate scenarios, passing "
        f"{robustness.scenarios_passed} of them (worst-case comfort: "
        f"{robustness.worst_case_comfort_percentage:.1f}%).",
    ]

    tradeoffs: list[str] = []
    if design.insulation_thickness_m >= 0.15:
        tradeoffs.append(
            f"Insulation thickness of {design.insulation_thickness_m:.2f} m improved thermal "
            f"performance but increases material usage and cost factor "
            f"({performance.material_cost_factor:.2f})."
        )
    if design.opening_area_m2 <= 2.0:
        tradeoffs.append(
            f"A smaller opening area ({design.opening_area_m2:.1f} m^2) reduced conductive heat "
            f"loss but also limits daylighting and solar gain "
            f"({performance.solar_gain_kwh:.1f} kWh) compared to designs with larger openings."
        )
    else:
        tradeoffs.append(
            f"The opening area of {design.opening_area_m2:.1f} m^2 increases solar gain "
            f"({performance.solar_gain_kwh:.1f} kWh) but also raises conductive heat loss "
            f"relative to a smaller-opening design."
        )
    if robustness.worst_case_comfort_percentage < robustness.average_comfort_percentage - 15:
        tradeoffs.append(
            f"Performance varies notably across scenarios (worst-case comfort "
            f"{robustness.worst_case_comfort_percentage:.1f}% versus average "
            f"{robustness.average_comfort_percentage:.1f}%), so auxiliary heating provisioning "
            f"should be sized for the worst case, not the average."
        )

    return RecommendationExplanation(headline=headline, reasons=reasons, tradeoffs=tradeoffs)
