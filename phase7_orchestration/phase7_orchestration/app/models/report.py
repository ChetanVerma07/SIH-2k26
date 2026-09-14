"""Engineering report data model."""
from typing import Any
from pydantic import BaseModel

from app.models.climate import ClimateProfile
from app.models.design import ShelterDesign
from app.models.results import (
    ThermalPerformance,
    BaselineComparison,
    RobustnessSummary,
    ConfidenceAssessment,
    ANSYSValidationResult,
    RecommendationExplanation,
)


class EngineeringReport(BaseModel):
    project: dict[str, Any]
    location: str
    climate: ClimateProfile
    design_input: dict[str, Any]
    simulation: dict[str, Any]
    recommended_design: ShelterDesign
    baseline_design: ShelterDesign
    results: ThermalPerformance
    baseline_results: ThermalPerformance
    comparison: BaselineComparison
    robustness: RobustnessSummary
    ansys_validation: ANSYSValidationResult | None
    confidence: ConfidenceAssessment
    recommendation: RecommendationExplanation
    assumptions: list[str]
    limitations: list[str]

    def to_markdown(self) -> str:
        d = self.recommended_design
        r = self.results
        b = self.baseline_results
        c = self.comparison
        rec = self.recommendation
        lines: list[str] = []
        lines.append(f"# Passive Shelter Design Report — {self.location}")
        lines.append("")
        lines.append("> **NOTE:** This report is generated using MOCK simulation components ")
        lines.append("> for orchestration-layer development. It is NOT validated engineering ")
        lines.append("> output. See Limitations section.")
        lines.append("")
        lines.append("## Project")
        for k, v in self.project.items():
            lines.append(f"- **{k}**: {v}")
        lines.append("")
        lines.append("## Climate")
        lines.append(f"- Location: {self.climate.location}")
        lines.append(f"- Climate zone: {self.climate.climate_zone}")
        lines.append(f"- Avg outdoor temp: {self.climate.avg_outdoor_temp_c:.1f} C")
        lines.append(
            f"- Range: {self.climate.min_outdoor_temp_c:.1f} C to {self.climate.max_outdoor_temp_c:.1f} C"
        )
        lines.append(f"- Avg solar radiation: {self.climate.avg_solar_radiation_wm2:.0f} W/m^2")
        lines.append(f"- Data source: {self.climate.source}")
        if self.climate.missing_fields:
            lines.append(f"- Missing/estimated fields: {', '.join(self.climate.missing_fields)}")
        lines.append("")
        lines.append("## Recommended Design")
        lines.append(f"- Dimensions: {d.dimensions_str}")
        lines.append(f"- Orientation: {d.orientation_deg:.0f} degrees")
        lines.append(f"- Wall material: {d.wall_material.value}")
        lines.append(f"- Roof material: {d.roof_material.value}")
        lines.append(f"- Floor material: {d.floor_material.value}")
        lines.append(f"- Insulation thickness: {d.insulation_thickness_m:.2f} m")
        lines.append(f"- Opening area: {d.opening_area_m2:.1f} m^2")
        lines.append("")
        lines.append("## Performance")
        lines.append(f"- Comfort: {r.comfort_percentage:.1f}%")
        lines.append(f"- Heat loss: {r.total_heat_loss_kwh:.1f} kWh")
        lines.append(f"- Solar gain: {r.solar_gain_kwh:.1f} kWh")
        lines.append(f"- Heating requirement: {r.estimated_heating_requirement_kwh:.1f} kWh")
        lines.append(f"- Overall score: {r.overall_score:.1f}")
        lines.append("")
        lines.append("## Baseline Comparison")
        lines.append(f"- Baseline heat loss: {b.total_heat_loss_kwh:.1f} kWh")
        lines.append(f"- Optimized heat loss: {r.total_heat_loss_kwh:.1f} kWh")
        lines.append(f"- Heat loss improvement: {c.heat_loss_improvement_percent:.1f}%")
        lines.append(f"- Baseline comfort: {c.baseline_comfort_percentage:.1f}%")
        lines.append(f"- Optimized comfort: {c.optimized_comfort_percentage:.1f}%")
        lines.append(f"- Comfort improvement: {c.comfort_improvement_points:.1f} percentage points")
        lines.append("")
        lines.append("## Robustness")
        lines.append(
            f"- Scenarios passed: {self.robustness.scenarios_passed}/{self.robustness.scenarios_evaluated}"
        )
        lines.append(f"- Worst-case comfort: {self.robustness.worst_case_comfort_percentage:.1f}%")
        lines.append(f"- Robustness score: {self.robustness.robustness_score:.1f}/100")
        for s in self.robustness.scenarios:
            lines.append(
                f"  - {s.scenario_name}: comfort {s.comfort_percentage:.1f}%, "
                f"heat loss {s.heat_loss_kwh:.1f} kWh, solar gain {s.solar_gain_kwh:.1f} kWh"
            )
        lines.append("")
        if self.ansys_validation:
            av = self.ansys_validation
            lines.append("## ANSYS Validation (MOCK)")
            lines.append(f"- Mock result: {av.is_mock}")
            lines.append(f"- Validated: {av.validated}")
            lines.append(f"- Notes: {av.notes}")
            lines.append("")
        lines.append("## Confidence")
        lines.append(f"- Data confidence: {self.confidence.data_confidence:.0f}%")
        lines.append(f"- Simulation confidence: {self.confidence.simulation_confidence:.0f}%")
        lines.append(f"- Recommendation confidence: {self.confidence.recommendation_confidence:.0f}%")
        lines.append(f"- {self.confidence.explanation}")
        lines.append("")
        lines.append("## Recommendation")
        lines.append(rec.headline)
        lines.append("")
        lines.append("### Reasons")
        for reason in rec.reasons:
            lines.append(f"- {reason}")
        lines.append("")
        lines.append("### Trade-offs")
        for t in rec.tradeoffs:
            lines.append(f"- {t}")
        lines.append("")
        lines.append("## Assumptions")
        for a in self.assumptions:
            lines.append(f"- {a}")
        lines.append("")
        lines.append("## Limitations")
        for lim in self.limitations:
            lines.append(f"- {lim}")
        lines.append("")
        return "\n".join(lines)
