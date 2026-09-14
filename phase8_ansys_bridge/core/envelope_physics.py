"""
Phase 8 - Shared envelope physics helpers.

Both the simplified lumped-capacitance model AND the mock ANSYS backend
derive the envelope's overall conductance (UA) and thermal capacitance
from the same design parameters, so that improving a design (more
insulation, more thermal mass, better shading) visibly improves BOTH the
"ANSYS" run and the simplified-model run -- exactly what a comparator is
supposed to be able to check agreement on.

The mock backend still applies its own small independent perturbation on
top of these shared values (see backend/mock_backend.py) to emulate the
fact that a full 3D ANSYS solve and a 1-node lumped model will never
match exactly, only agree within engineering tolerance.
"""

from __future__ import annotations

from config import ShelterDesignParams

# Rough volumetric heat capacity (J / m3-K) by material, used to derive a
# physically grounded thermal capacitance from actual wall/roof thickness
# rather than an arbitrary flat constant. Approximate literature values.
_VOLUMETRIC_HEAT_CAPACITY_J_M3K = {
    "fired_brick": 1.7e6,
    "stabilized_mud_block": 1.3e6,
    "compressed_earth_block": 1.3e6,
    "rcc_slab": 2.0e6,
    "rcc_slab_with_insulation": 1.8e6,
    "concrete_block": 1.9e6,
    "aac_block": 0.9e6,
}
_DEFAULT_VOLUMETRIC_HEAT_CAPACITY = 1.5e6

# Fraction of the raw fabric heat capacity that is actually thermally
# "active" within a daily cycle -- insulation placement, exposed vs.
# rendered surfaces, etc. all affect this in reality; here it is driven by
# the design's declared thermal_mass_class.
_MASS_CLASS_ACTIVE_FRACTION = {"low": 0.35, "medium": 0.6, "high": 0.9}


def _volumetric_heat_capacity(material: str) -> float:
    return _VOLUMETRIC_HEAT_CAPACITY_J_M3K.get(material, _DEFAULT_VOLUMETRIC_HEAT_CAPACITY)


def envelope_ua(design: ShelterDesignParams) -> float:
    """Overall conductance (U*A) of the envelope in W/K."""
    wall_r = design.wall_thickness_m / max(design.wall_conductivity_w_mk, 1e-6)
    wall_r += design.insulation_r_value_m2k_w
    wall_u = 1.0 / max(wall_r, 1e-6)

    # Added insulation is assumed to protect the roof as well as the walls
    # (a design that specifies insulation_r_value_m2k_w > 0 is treated as
    # an insulated envelope overall, not wall-only).
    roof_r = design.roof_thickness_m / max(design.roof_conductivity_w_mk, 1e-6)
    roof_r += design.insulation_r_value_m2k_w
    roof_u = 1.0 / max(roof_r, 1e-6)

    ua_wall = wall_u * design.wall_area_m2
    ua_roof = roof_u * design.roof_area_m2
    ua_window = design.window_u_value_w_m2k * design.window_area_m2

    volume_m3 = design.floor_area_m2 * 3.0
    ua_vent = 0.33 * design.ventilation_ach * volume_m3

    return ua_wall + ua_roof + ua_window + ua_vent


def thermal_capacitance(design: ShelterDesignParams) -> float:
    """Effective thermal mass of the zone fabric, in J/K.

    Derived from actual material, thickness and area (not an arbitrary
    constant), then scaled by how much of that fabric mass is thermally
    "active" within a daily cycle (thermal_mass_class).
    """
    c_wall = (_volumetric_heat_capacity(design.wall_material)
              * design.wall_thickness_m * design.wall_area_m2)
    c_roof = (_volumetric_heat_capacity(design.roof_material)
              * design.roof_thickness_m * design.roof_area_m2)

    active_fraction = _MASS_CLASS_ACTIVE_FRACTION.get(design.thermal_mass_class, 0.6)

    # small allowance for room air + furnishings, so capacitance is never zero
    air_capacitance = 1200.0 * 1005.0 * design.floor_area_m2 * 3.0 * 1e-3

    return active_fraction * (c_wall + c_roof) + air_capacitance


def solar_gain_params(design: ShelterDesignParams) -> tuple:
    """Returns (solar_absorptance, effective_solar_area_m2)."""
    solar_absorptance = 0.6 * design.shading_coefficient
    effective_solar_area = design.window_area_m2 + 0.15 * design.wall_area_m2
    return solar_absorptance, effective_solar_area
