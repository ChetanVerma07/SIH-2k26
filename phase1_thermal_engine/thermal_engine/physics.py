"""
physics.py
==========

Pure heat-transfer functions used by the simulation engine.

These functions contain no simulation state or looping logic -- they take
physical quantities in and return physical quantities out, so they can be
unit-tested independently of the time-stepping simulation in
``simulation.py``.

Equations used (all SI units)
------------------------------

Conductive heat flow through a surface:

    Q = U * A * (T_indoor - T_outdoor)          [W]

    where U is the overall heat-transfer coefficient of the surface,
    W/(m^2.K), A is the surface area, m^2, and T_indoor/T_outdoor are in
    the same temperature unit (Celsius or Kelvin -- only the difference
    matters).

    Sign convention used throughout this engine: Q > 0 means heat is
    LEAVING the shelter (indoor warmer than outdoor). This lets all
    conduction terms be summed directly into a single "total heat loss".

Solar heat gain on an opaque, sun-exposed surface:

    Q_solar = I * A_eff * alpha                  [W]

    where I is incident solar radiation, W/m^2, A_eff is the effective
    sun-exposed area, m^2, and alpha is the surface's solar absorptivity
    (dimensionless, 0-1).

Lumped thermal-mass temperature update (explicit Euler):

    dT = (Q_solar - Q_loss_total) * dt / C

    where C is the shelter's total thermal (heat) capacity, J/K, and dt is
    the simulation timestep, s.
"""

from __future__ import annotations

from .validation import validate_non_negative, validate_positive


def u_value_single_layer(thermal_conductivity: float, thickness: float) -> float:
    """
    Compute the conductive U-value of a single homogeneous layer.

    Args:
        thermal_conductivity: k, in W/(m.K). Must be > 0.
        thickness: layer thickness, in m. Must be > 0.

    Returns:
        U-value in W/(m^2.K), equal to k / thickness.
    """
    validate_positive(thermal_conductivity, "thermal_conductivity")
    validate_positive(thickness, "thickness")
    return thermal_conductivity / thickness


def conduction_heat_flow(
    u_value: float, area: float, indoor_temp: float, outdoor_temp: float
) -> float:
    """
    Conductive heat flow through a surface: Q = U * A * (T_in - T_out).

    Args:
        u_value: overall heat-transfer coefficient, W/(m^2.K). Must be >= 0.
        area: surface area, m^2. Must be >= 0.
        indoor_temp: indoor air temperature, C (or K).
        outdoor_temp: outdoor/ambient air temperature, same unit as indoor.

    Returns:
        Heat flow in Watts. Positive means heat leaving the shelter
        (indoor warmer than outdoor); negative means heat entering.
    """
    validate_non_negative(u_value, "u_value")
    validate_non_negative(area, "area")
    return u_value * area * (indoor_temp - outdoor_temp)


def solar_heat_gain(
    solar_radiation: float, effective_area: float, solar_absorptivity: float
) -> float:
    """
    Solar heat gain on a sun-exposed surface: Q = I * A_eff * alpha.

    Args:
        solar_radiation: incident solar radiation, W/m^2. Must be >= 0.
        effective_area: effective sun-exposed area, m^2. Must be >= 0.
        solar_absorptivity: fraction of radiation absorbed, in [0, 1].

    Returns:
        Absorbed solar power in Watts (always >= 0).
    """
    validate_non_negative(solar_radiation, "solar_radiation")
    validate_non_negative(effective_area, "effective_area")
    if not (0.0 <= solar_absorptivity <= 1.0):
        raise ValueError(
            f"'solar_absorptivity' must be in [0, 1], got {solar_absorptivity!r}."
        )
    return solar_radiation * effective_area * solar_absorptivity


def temperature_change(
    net_heat_flow: float, thermal_capacity: float, timestep_seconds: float
) -> float:
    """
    Lumped-capacitance temperature change over one timestep.

    dT = net_heat_flow * dt / C

    Args:
        net_heat_flow: net power INTO the shelter, W (solar gain minus
            total heat loss). Positive warms the shelter.
        thermal_capacity: total effective heat capacity of the shelter's
            thermal mass, J/K. Must be > 0.
        timestep_seconds: simulation timestep, s. Must be > 0.

    Returns:
        Temperature change over the timestep, in the same unit as the
        capacity's reference temperature (Celsius degrees, i.e. Kelvin).
    """
    validate_positive(thermal_capacity, "thermal_capacity")
    validate_positive(timestep_seconds, "timestep_seconds")
    return net_heat_flow * timestep_seconds / thermal_capacity
