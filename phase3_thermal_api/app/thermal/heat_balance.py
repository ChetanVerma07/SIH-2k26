"""
Heat balance assembly.

Combines conduction losses through walls, roof, floor, and openings with
solar gain to produce the net heat flow into the indoor air node:

    Q_net = Q_solar - (Q_wall + Q_roof + Q_floor + Q_opening)

All Q values below are instantaneous heat FLOWS in Watts. A positive
*_heat_loss means heat is leaving the shelter (indoor warmer than the
relevant outside reference temperature); it can be negative, meaning heat
is actually flowing inward (e.g. a cold shelter warmed by hot ambient air).
"""
from __future__ import annotations

from dataclasses import dataclass

from app.models.material import assembly_u_value
from app.models.shelter import ShelterConfig
from app.thermal.conduction import conductive_heat_flow
from app.thermal.solar import total_solar_gain


@dataclass
class HeatBalanceResult:
    solar_gain: float
    wall_heat_loss: float
    roof_heat_loss: float
    floor_heat_loss: float
    opening_heat_loss: float
    total_heat_loss: float
    net_heat_flow: float


def compute_heat_balance(
    shelter: ShelterConfig,
    indoor_temperature: float,
    ambient_temperature: float,
    ground_temperature: float,
    solar_radiation: float,
) -> HeatBalanceResult:
    """
    Compute all instantaneous heat flows (W) for one point in time.

    Conduction losses use Q = U * A * dT with dT = indoor - outside_ref,
    where outside_ref is ambient_temperature for walls/roof/openings and
    ground_temperature for the floor (floors exchange heat with the
    ground/sub-floor rather than the open air - see README).
    """
    u_wall = assembly_u_value(shelter.wall_material)
    u_roof = assembly_u_value(shelter.roof_material)
    u_floor = assembly_u_value(shelter.floor_material)
    u_opening = shelter.openings.opening_u_value

    wall_loss = conductive_heat_flow(
        u_wall, shelter.net_wall_area, indoor_temperature - ambient_temperature
    )
    roof_loss = conductive_heat_flow(
        u_roof, shelter.roof_area, indoor_temperature - ambient_temperature
    )
    floor_loss = conductive_heat_flow(
        u_floor, shelter.floor_area, indoor_temperature - ground_temperature
    )
    opening_loss = conductive_heat_flow(
        u_opening, shelter.openings.total_area, indoor_temperature - ambient_temperature
    )

    total_loss = wall_loss + roof_loss + floor_loss + opening_loss
    solar_gain = total_solar_gain(solar_radiation, shelter)
    net_flow = solar_gain - total_loss

    return HeatBalanceResult(
        solar_gain=solar_gain,
        wall_heat_loss=wall_loss,
        roof_heat_loss=roof_loss,
        floor_heat_loss=floor_loss,
        opening_heat_loss=opening_loss,
        total_heat_loss=total_loss,
        net_heat_flow=net_flow,
    )


def effective_thermal_mass(shelter: ShelterConfig) -> float:
    """
    Effective heat capacity of the indoor air node, J/K.

    C_total = C_air + structural_mass_fraction * C_structure

    C_air is the sensible heat capacity of the indoor air volume.
    C_structure is the areal heat capacity of walls+roof+floor multiplied
    by their respective areas, scaled by `structural_mass_fraction` to
    represent the portion of the structure's mass that is thermally
    coupled closely enough to the indoor air to respond within a
    simulation timestep (a lumped-capacitance simplification - see
    README "Limitations").
    """
    from app.models.material import assembly_areal_heat_capacity

    air_density = 1.2  # kg/m^3
    air_specific_heat = 1005.0  # J/(kg*K)
    c_air = air_density * air_specific_heat * shelter.volume

    c_walls = assembly_areal_heat_capacity(shelter.wall_material) * shelter.net_wall_area
    c_roof = assembly_areal_heat_capacity(shelter.roof_material) * shelter.roof_area
    c_floor = assembly_areal_heat_capacity(shelter.floor_material) * shelter.floor_area
    c_structure = (c_walls + c_roof + c_floor) * shelter.structural_mass_fraction

    return c_air + c_structure
