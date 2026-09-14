"""
Solar thermal gain.

Core equation:

    Q_solar = Solar_Radiation * Effective_Area * Solar_Absorptivity

Applied to three surfaces:

1. ROOF - always assumed to face the sky, so it receives the full supplied
   solar_radiation with no orientation factor.
2. FRONT FACADE - the single wall assumed to face `orientation`. Its
   exposure is scaled by an orientation_factor in [0.2, 1.0] (see
   app.models.shelter.ORIENTATION_SOLAR_FACTOR). Only the opaque portion of
   that facade (its area minus its assumed share of openings) absorbs solar
   radiation as heat via solar_absorptivity.
3. WINDOWS on the front facade - modeled separately using a Solar Heat Gain
   Coefficient (SHGC) rather than absorptivity, since most incident
   radiation is *transmitted* through glazing rather than absorbed by it.
   Doors and other opaque openings are not given a solar gain term in this
   simplified model (their absorptivity is unknown/variable and their area
   is typically small).

This is a simplification, not a full solar-geometry / sun-path model - see
README "Orientation" and "Limitations" sections.
"""
from __future__ import annotations

from app.models.material import MaterialAssembly, assembly_solar_absorptivity
from app.models.shelter import ShelterConfig


def roof_solar_gain(solar_radiation: float, roof_area: float, roof_material: MaterialAssembly) -> float:
    absorptivity = assembly_solar_absorptivity(roof_material)
    return solar_radiation * roof_area * absorptivity


def wall_solar_gain(
    solar_radiation: float,
    shelter: ShelterConfig,
) -> float:
    """Solar gain absorbed by the opaque portion of the front facade."""
    orientation_factor = shelter.orientation.solar_factor
    opaque_area = max(
        shelter.front_facade_area - shelter.front_facade_opening_share, 0.0
    )
    absorptivity = assembly_solar_absorptivity(shelter.wall_material)
    return solar_radiation * orientation_factor * opaque_area * absorptivity


def window_solar_gain(solar_radiation: float, shelter: ShelterConfig) -> float:
    """Direct solar gain transmitted through windows on the front facade."""
    orientation_factor = shelter.orientation.solar_factor
    # Assume windows, like other openings, are distributed evenly across
    # the four facades - only the front-facade share is sun-facing.
    front_window_area = shelter.openings.window_area / 4.0
    shgc = shelter.openings.window_shgc
    return solar_radiation * orientation_factor * front_window_area * shgc


def total_solar_gain(solar_radiation: float, shelter: ShelterConfig) -> float:
    """Total instantaneous solar gain (roof + opaque wall + windows), W."""
    q_roof = roof_solar_gain(solar_radiation, shelter.roof_area, shelter.roof_material)
    q_wall = wall_solar_gain(solar_radiation, shelter)
    q_window = window_solar_gain(solar_radiation, shelter)
    return q_roof + q_wall + q_window
