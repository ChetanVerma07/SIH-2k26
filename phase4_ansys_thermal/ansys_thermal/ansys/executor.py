"""
Lumped-parameter thermal network solver.

This module implements a SIMPLIFIED, explicit-time-stepping lumped
thermal-mass model of a shelter. It is used exclusively by
``MockThermalAdapter`` to produce a plausible, physically-motivated
demonstration result WITHOUT requiring ANSYS.

This is deliberately NOT a finite-element solver and NOT a substitute
for ANSYS. It models:

    - a single lumped indoor air node with thermal capacitance
    - conductive heat exchange through walls, roof, floor and
      openings, each treated as a 1-D resistance (external convection
      -> conduction -> internal convection, in series)
    - direct solar heat gain through openings (transmitted solar) and
      absorbed solar heat flux on opaque exterior surfaces (which
      raises the effective outdoor surface temperature via a
      sol-air-temperature approximation)
    - a floor boundary that exchanges heat with a fixed ground
      temperature

The engineering assumptions are documented inline. This model is
intended to give order-of-magnitude, physically sensible behaviour
for demonstration/testing, not certified thermal performance figures.
Final figures MUST be validated in ANSYS.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any

from ansys_thermal.models.simulation import SimulationConfig
from ansys_thermal.geometry.shelter_builder import build_rectangular_shelter, ShelterElement

AIR_DENSITY_KG_M3 = 1.2
AIR_SPECIFIC_HEAT_J_KGK = 1005.0


@dataclass
class TimeStepResult:
    hour: float
    ambient_temp_c: float
    indoor_temp_c: float
    solar_irradiance_w_m2: float
    total_heat_flow_w: float  # net heat flow INTO the indoor air node
    solar_gain_w: float
    surface_heat_flow_w: Dict[str, float]  # per-element-type heat flow, W (+ = into building)


def _material_for_element(el: ShelterElement, config: SimulationConfig):
    if el.element_type == "wall":
        return config.materials.wall_material
    if el.element_type == "roof":
        return config.materials.roof_material
    if el.element_type == "floor":
        return config.materials.floor_material
    if el.element_type == "opening":
        return config.materials.window_material
    raise ValueError(f"Unknown element type: {el.element_type}")


def _element_conductance_w_k(el: ShelterElement, config: SimulationConfig) -> float:
    """Overall (U*A) conductance for one element, combining external
    convection, conduction through the element thickness, and internal
    convection as three resistances in series (a standard simplified
    building-physics approach). Units: W/K.
    """
    bc = config.boundary_conditions
    mat = _material_for_element(el, config)

    if el.area_m2 <= 0:
        return 0.0

    r_ext = 1.0 / bc.external_convection_w_m2k  # m^2.K/W
    r_cond = el.thickness_m / mat.thermal_conductivity_w_mk  # m^2.K/W
    r_int = 1.0 / bc.internal_convection_w_m2k  # m^2.K/W

    r_total = r_ext + r_cond + r_int  # m^2.K/W
    u_value = 1.0 / r_total  # W/m^2.K
    return u_value * el.area_m2  # W/K


def _floor_conductance_w_k(el: ShelterElement, config: SimulationConfig) -> float:
    """Floor is treated as exchanging with ground temperature through
    conduction + internal convection only (no external convection,
    since it is on-grade)."""
    bc = config.boundary_conditions
    mat = _material_for_element(el, config)
    if el.area_m2 <= 0:
        return 0.0
    r_cond = el.thickness_m / mat.thermal_conductivity_w_mk
    r_int = 1.0 / bc.internal_convection_w_m2k
    r_total = r_cond + r_int
    u_value = 1.0 / r_total
    return u_value * el.area_m2


def run_lumped_thermal_simulation(config: SimulationConfig) -> List[TimeStepResult]:
    """Run the explicit-time-stepping lumped thermal model over the
    full boundary-condition time series and return per-step results.
    """
    plan = build_rectangular_shelter(config.geometry)
    bc = config.boundary_conditions

    wall_els = [e for e in plan.elements if e.element_type == "wall"]
    roof_els = [e for e in plan.elements if e.element_type == "roof"]
    floor_els = [e for e in plan.elements if e.element_type == "floor"]
    opening_els = [e for e in plan.elements if e.element_type == "opening"]

    wall_conductance = sum(_element_conductance_w_k(e, config) for e in wall_els)
    roof_conductance = sum(_element_conductance_w_k(e, config) for e in roof_els)
    opening_conductance = sum(_element_conductance_w_k(e, config) for e in opening_els)
    floor_conductance = sum(_floor_conductance_w_k(e, config) for e in floor_els)

    # Indoor air thermal capacitance (J/K). This is a simplification:
    # only the air mass is modelled as a capacitance; wall thermal mass
    # is implicitly represented only through steady-state conduction,
    # not transient storage. This is documented as a modelling
    # simplification of the mock adapter, not an ANSYS result.
    air_capacitance = (
        AIR_DENSITY_KG_M3 * AIR_SPECIFIC_HEAT_J_KGK * plan.internal_volume_m3
    )
    # Add a fraction of wall thermal mass to avoid an unrealistically
    # fast-responding air node (documented approximation).
    wall_area_total = sum(e.area_m2 for e in wall_els) + sum(e.area_m2 for e in roof_els)
    thermal_mass_layer_m = 0.05  # effective mass-coupled layer thickness, documented assumption
    wall_mat = config.materials.wall_material
    wall_mass_capacitance = (
        wall_area_total
        * thermal_mass_layer_m
        * wall_mat.density_kg_m3
        * wall_mat.specific_heat_j_kgk
    )
    total_capacitance = air_capacitance + wall_mass_capacitance

    indoor_temp = bc.indoor_initial_temp_c
    results: List[TimeStepResult] = []

    series = bc.ambient_series
    for idx in range(len(series) - 1):
        pt = series[idx]
        next_pt = series[idx + 1]
        dt = (next_pt.hour - pt.hour) * 3600.0
        if dt <= 0:
            dt = bc.time_step_s

        ambient = pt.ambient_temp_c
        solar = pt.solar_irradiance_w_m2

        # --- Conductive exchange (opaque + opening elements) ---
        wall_heat = wall_conductance * (ambient - indoor_temp)
        roof_heat = roof_conductance * (ambient - indoor_temp)
        opening_conductive_heat = opening_conductance * (ambient - indoor_temp)
        floor_heat = floor_conductance * (bc.ground_temp_c - indoor_temp)

        # --- Solar gain ---
        # 1) Direct solar gain through openings (simplified: assume a
        #    transmittance of (1 - solar_absorptivity_window) as a
        #    rough proxy for glazing transmittance in absence of a
        #    dedicated transmittance property).
        window_mat = config.materials.window_material
        glazing_transmittance = max(0.0, 1.0 - window_mat.solar_absorptivity)
        opening_area_total = sum(e.area_m2 for e in opening_els)
        solar_gain_openings = solar * opening_area_total * glazing_transmittance

        # 2) Absorbed solar on opaque exterior surfaces raises their
        #    effective sol-air temperature, increasing conduction into
        #    the building. Approximate as extra heat flow proportional
        #    to absorbed irradiance and surface area, moderated by the
        #    external film resistance (standard sol-air approximation).
        wall_mat_local = config.materials.wall_material
        roof_mat_local = config.materials.roof_material
        wall_area_total_only = sum(e.area_m2 for e in wall_els)
        roof_area_total_only = sum(e.area_m2 for e in roof_els)

        sol_air_wall_boost = (
            wall_mat_local.solar_absorptivity
            * solar
            * wall_area_total_only
            / bc.external_convection_w_m2k
        ) * (wall_conductance / max(wall_area_total_only, 1e-9)) if wall_area_total_only > 0 else 0.0
        sol_air_roof_boost = (
            roof_mat_local.solar_absorptivity
            * solar
            * roof_area_total_only
            / bc.external_convection_w_m2k
        ) * (roof_conductance / max(roof_area_total_only, 1e-9)) if roof_area_total_only > 0 else 0.0

        solar_gain_opaque = sol_air_wall_boost + sol_air_roof_boost
        total_solar_gain = solar_gain_openings + solar_gain_opaque

        net_heat_flow = (
            wall_heat
            + roof_heat
            + opening_conductive_heat
            + floor_heat
            + total_solar_gain
        )

        # Explicit Euler update of indoor air (+ coupled mass) temperature.
        d_temp = (net_heat_flow * dt) / total_capacitance
        indoor_temp = indoor_temp + d_temp

        results.append(
            TimeStepResult(
                hour=pt.hour,
                ambient_temp_c=round(ambient, 4),
                indoor_temp_c=round(indoor_temp, 4),
                solar_irradiance_w_m2=round(solar, 2),
                total_heat_flow_w=round(net_heat_flow, 3),
                solar_gain_w=round(total_solar_gain, 3),
                surface_heat_flow_w={
                    "wall": round(wall_heat, 3),
                    "roof": round(roof_heat, 3),
                    "floor": round(floor_heat, 3),
                    "opening": round(opening_conductive_heat, 3),
                },
            )
        )

    # Append a final point mirroring the last computed state at the
    # last time stamp, so time_series length matches ambient_series.
    if results:
        last = results[-1]
        final_pt = series[-1]
        results.append(
            TimeStepResult(
                hour=final_pt.hour,
                ambient_temp_c=round(final_pt.ambient_temp_c, 4),
                indoor_temp_c=last.indoor_temp_c,
                solar_irradiance_w_m2=round(final_pt.solar_irradiance_w_m2, 2),
                total_heat_flow_w=last.total_heat_flow_w,
                solar_gain_w=last.solar_gain_w,
                surface_heat_flow_w=dict(last.surface_heat_flow_w),
            )
        )

    return results
