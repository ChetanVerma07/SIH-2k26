"""Deterministic mock thermal simulator.

This is NOT a validated engineering simulation (no EnergyPlus/ANSYS/CFD).
It implements a simplified, transparent hour-by-hour heat-balance model so
that design changes produce physically-sensible, deterministic, and
explainable results:

  - more insulation           -> lower conductance -> lower heat loss
  - larger openings           -> more solar gain AND more conductive loss
  - lower-conductivity walls  -> lower heat loss
  - higher solar radiation    -> higher solar gain
  - orientation               -> changes effective solar gain

All physical constants below are illustrative approximations chosen for
orchestration-layer development, not validated material properties.
"""
import math

from app.interfaces.thermal import ThermalSimulator
from app.models.climate import ClimateProfile
from app.models.design import (
    ShelterDesign,
    MATERIAL_CONDUCTIVITY,
    MATERIAL_COST_FACTOR,
    RoofMaterial,
    FloorMaterial,
)
from app.models.request import ComfortRange
from app.models.results import ThermalPerformance

# Illustrative constants (documented, not validated engineering data)
BASE_WALL_THICKNESS_M = 0.30
INSULATION_CONDUCTIVITY_WMK = 0.035
SURFACE_RESISTANCE_M2K_PER_W = 0.17
OPENING_U_VALUE_WM2K = 2.8
SOLAR_HEAT_GAIN_COEFFICIENT = 0.60

ROOF_U_VALUE_WM2K = {
    RoofMaterial.THATCH: 1.5,
    RoofMaterial.INSULATED_METAL: 0.4,
    RoofMaterial.EARTH_ROOF: 0.6,
    RoofMaterial.TIMBER_INSULATED: 0.3,
}

FLOOR_U_VALUE_WM2K = {
    FloorMaterial.COMPACTED_EARTH: 1.2,
    FloorMaterial.INSULATED_CONCRETE: 0.5,
    FloorMaterial.RAISED_TIMBER: 0.7,
}

# Weights for the transparent composite score. Documented so scoring is
# auditable rather than a black box.
SCORE_WEIGHT_HEATING_PER_M2 = 0.5
SCORE_WEIGHT_COST_FACTOR = 0.1


def _orientation_factor(orientation_deg: float) -> float:
    """South-facing (180 deg) is assumed most favorable for solar gain in the
    northern hemisphere. Returns a value in [0, 1]."""
    return 0.5 + 0.5 * math.cos(math.radians(orientation_deg - 180.0))


def _wall_u_value(design: ShelterDesign) -> float:
    wall_k = MATERIAL_CONDUCTIVITY[design.wall_material]
    r_wall_material = BASE_WALL_THICKNESS_M / wall_k
    r_insulation = design.insulation_thickness_m / INSULATION_CONDUCTIVITY_WMK
    r_total = r_wall_material + r_insulation + SURFACE_RESISTANCE_M2K_PER_W
    return 1.0 / r_total


def _total_ua_wk(design: ShelterDesign) -> float:
    """Total conductance (W/K) of the shelter envelope."""
    u_wall = _wall_u_value(design)
    net_wall_area = max(design.wall_area_m2 - design.opening_area_m2, 0.0)
    ua_wall = u_wall * net_wall_area
    ua_opening = OPENING_U_VALUE_WM2K * design.opening_area_m2
    ua_roof = ROOF_U_VALUE_WM2K[design.roof_material] * design.floor_area_m2
    ua_floor = FLOOR_U_VALUE_WM2K[design.floor_material] * design.floor_area_m2
    return ua_wall + ua_opening + ua_roof + ua_floor


class MockThermalSimulator(ThermalSimulator):
    def simulate(
        self,
        design: ShelterDesign,
        climate: ClimateProfile,
        comfort_range: ComfortRange,
        duration_hours: int,
        outdoor_temp_offset_c: float = 0.0,
        solar_radiation_factor: float = 1.0,
    ) -> ThermalPerformance:
        ua_total = _total_ua_wk(design)
        orientation_factor = _orientation_factor(design.orientation_deg)
        avg_outdoor = climate.avg_outdoor_temp_c + outdoor_temp_offset_c
        temp_amplitude = (climate.max_outdoor_temp_c - climate.min_outdoor_temp_c) / 2.0
        solar_avg = climate.avg_solar_radiation_wm2 * solar_radiation_factor

        # Insulation dampens the passive indoor temperature's tracking of
        # outdoor swings (a simple thermal-mass proxy) via an exponential
        # smoothing factor.
        alpha = max(0.2, min(0.9, 0.9 - design.insulation_thickness_m * 1.5))

        # Heat loss / heating requirement are computed degree-day style
        # against a fixed setpoint (the comfort-range midpoint), so they
        # depend only on envelope conductance (UA) and outdoor conditions —
        # NOT on the passive indoor temperature below. This keeps "more
        # insulation -> lower heat loss" a direct, monotonic relationship
        # instead of being masked by solar-driven indoor temperature rise.
        setpoint_c = (comfort_range.min_c + comfort_range.max_c) / 2.0

        indoor_temps: list[float] = []
        heat_loss_wh_total = 0.0
        solar_gain_wh_total = 0.0
        heating_required_wh_total = 0.0
        prev_indoor: float | None = None

        for hour in range(duration_hours):
            hour_of_day = hour % 24
            # Outdoor temp follows a daily sinusoid, trough ~4am, peak ~4pm
            outdoor_h = avg_outdoor + temp_amplitude * math.sin(
                2 * math.pi * (hour_of_day - 10) / 24
            )
            # Daylight bell curve between roughly 6:00 and 18:00
            if 6 <= hour_of_day <= 18:
                daylight_factor = math.sin(math.pi * (hour_of_day - 6) / 12)
            else:
                daylight_factor = 0.0

            solar_w = (
                solar_avg
                * daylight_factor
                * orientation_factor
                * SOLAR_HEAT_GAIN_COEFFICIENT
                * design.opening_area_m2
            )
            solar_gain_wh_total += solar_w  # 1 hour steps -> Wh

            # Conductive heat loss needed to hold the setpoint against the
            # outdoor temperature this hour (before considering solar offset).
            gross_loss_w = ua_total * max(0.0, setpoint_c - outdoor_h)
            heat_loss_wh_total += gross_loss_w
            # Auxiliary heating still required after solar contribution offsets
            # part of the conductive loss.
            heating_required_wh_total += max(0.0, gross_loss_w - solar_w)

            # Passive indoor temperature (no auxiliary heating) — used only
            # for comfort/min/max/avg reporting, not for the loss calc above.
            delta_t_from_solar = solar_w / ua_total if ua_total > 0 else 0.0
            raw_indoor = outdoor_h + delta_t_from_solar

            if prev_indoor is None:
                indoor_h = raw_indoor
            else:
                indoor_h = alpha * raw_indoor + (1 - alpha) * prev_indoor
            prev_indoor = indoor_h
            indoor_temps.append(indoor_h)

        avg_indoor = sum(indoor_temps) / len(indoor_temps)
        min_indoor = min(indoor_temps)
        max_indoor = max(indoor_temps)
        hours_in_comfort = sum(
            1 for t in indoor_temps if comfort_range.min_c <= t <= comfort_range.max_c
        )
        comfort_percentage = 100.0 * hours_in_comfort / len(indoor_temps)

        total_heat_loss_kwh = heat_loss_wh_total / 1000.0
        solar_gain_kwh = solar_gain_wh_total / 1000.0
        heating_requirement_kwh = heating_required_wh_total / 1000.0
        net_thermal_energy_kwh = solar_gain_kwh - total_heat_loss_kwh

        material_cost_factor = round(
            MATERIAL_COST_FACTOR[design.wall_material]
            * (1.0 + design.insulation_thickness_m)
            * design.floor_area_m2
            / 10.0,
            2,
        )

        heating_per_m2 = heating_requirement_kwh / max(design.floor_area_m2, 1.0)
        overall_score = (
            comfort_percentage
            - SCORE_WEIGHT_HEATING_PER_M2 * heating_per_m2
            - SCORE_WEIGHT_COST_FACTOR * material_cost_factor
        )

        return ThermalPerformance(
            design_id=design.design_id,
            avg_indoor_temp_c=round(avg_indoor, 2),
            min_indoor_temp_c=round(min_indoor, 2),
            max_indoor_temp_c=round(max_indoor, 2),
            comfort_percentage=round(comfort_percentage, 2),
            total_heat_loss_kwh=round(total_heat_loss_kwh, 2),
            solar_gain_kwh=round(solar_gain_kwh, 2),
            net_thermal_energy_kwh=round(net_thermal_energy_kwh, 2),
            estimated_heating_requirement_kwh=round(heating_requirement_kwh, 2),
            material_cost_factor=material_cost_factor,
            overall_score=round(overall_score, 2),
        )
