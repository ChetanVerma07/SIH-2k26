"""Single-parameter what-if analysis."""
from app.interfaces.thermal import ThermalSimulator
from app.models.climate import ClimateProfile
from app.models.design import ShelterDesign, WallMaterial
from app.models.request import ComfortRange
from app.models.results import WhatIfResult

_MUTABLE_NUMERIC_FIELDS = {"insulation_thickness_m", "window_area_m2", "orientation_deg"}


def apply_what_if(
    base_design: ShelterDesign,
    parameter: str,
    new_value: float | str,
    climate: ClimateProfile,
    comfort_range: ComfortRange,
    duration_hours: int,
    thermal_simulator: ThermalSimulator,
) -> WhatIfResult:
    design_dict = base_design.model_dump()

    if parameter == "window_area_m2":
        original_value: float | str = base_design.opening_area_m2
        design_dict["opening_area_m2"] = float(new_value)
    elif parameter == "insulation_thickness_m":
        original_value = base_design.insulation_thickness_m
        design_dict["insulation_thickness_m"] = float(new_value)
    elif parameter == "orientation_deg":
        original_value = base_design.orientation_deg
        design_dict["orientation_deg"] = float(new_value) % 360.0
    elif parameter == "wall_material":
        original_value = base_design.wall_material.value
        design_dict["wall_material"] = WallMaterial(new_value)
    else:
        raise ValueError(f"Unsupported what-if parameter: {parameter}")

    design_dict["design_id"] = f"{base_design.design_id}-whatif"
    modified_design = ShelterDesign(**design_dict)

    baseline_perf = thermal_simulator.simulate(
        design=base_design,
        climate=climate,
        comfort_range=comfort_range,
        duration_hours=duration_hours,
    )
    modified_perf = thermal_simulator.simulate(
        design=modified_design,
        climate=climate,
        comfort_range=comfort_range,
        duration_hours=duration_hours,
    )

    heat_loss_change = modified_perf.total_heat_loss_kwh - baseline_perf.total_heat_loss_kwh
    comfort_change = modified_perf.comfort_percentage - baseline_perf.comfort_percentage
    solar_gain_change = modified_perf.solar_gain_kwh - baseline_perf.solar_gain_kwh
    score_change = modified_perf.overall_score - baseline_perf.overall_score

    narrative = (
        f"Changing {parameter} from {original_value} to {new_value} changed heat loss by "
        f"{heat_loss_change:+.2f} kWh, comfort by {comfort_change:+.2f} percentage points, "
        f"solar gain by {solar_gain_change:+.2f} kWh, and overall score by {score_change:+.2f}."
    )

    return WhatIfResult(
        parameter=parameter,
        original_value=original_value,
        new_value=new_value,
        heat_loss_change_kwh=round(heat_loss_change, 2),
        comfort_change_points=round(comfort_change, 2),
        solar_gain_change_kwh=round(solar_gain_change, 2),
        score_change=round(score_change, 2),
        narrative=narrative,
    )
