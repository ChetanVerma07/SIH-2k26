"""
comparison.py
=============

Utility for simulating several shelter designs under identical
environmental conditions and comparing their thermal performance.

This is a plain simulate-and-tabulate comparison, intended as the data
foundation that a later optimisation engine (e.g. a genetic algorithm or
Bayesian optimiser sweeping material/geometry choices) would build on top
of. No optimisation or search is implemented in this phase.
"""

from __future__ import annotations

import pandas as pd

from .shelter import Shelter
from .simulation import TimeSeriesInput, simulate_shelter
from .validation import validate_non_empty_string


def compare_designs(
    designs: dict[str, Shelter],
    ambient_temperature: TimeSeriesInput,
    solar_radiation: TimeSeriesInput,
    duration_hours: float,
    time_step_hours: float = 1.0,
    comfort_range: tuple[float, float] | None = None,
) -> pd.DataFrame:
    """
    Simulate multiple shelter designs under the same conditions and return
    a comparison table.

    Args:
        designs: Mapping of design label -> :class:`Shelter`. Must contain
            at least one entry.
        ambient_temperature: Same as in :func:`simulate_shelter`, applied
            identically to every design.
        solar_radiation: Same as in :func:`simulate_shelter`, applied
            identically to every design.
        duration_hours: Simulated duration, in hours.
        time_step_hours: Simulation timestep, in hours.
        comfort_range: Optional (min, max) indoor comfort band in Celsius.

    Returns:
        A ``pandas.DataFrame`` indexed by design label, with one row per
        design and columns:

        - average_indoor_temperature (C)
        - minimum_indoor_temperature (C)
        - maximum_indoor_temperature (C)
        - total_solar_energy_wh
        - total_heat_loss_wh
        - net_energy_balance_wh
        - time_in_comfort_hours (NaN if no comfort_range given)
        - fraction_time_in_comfort (NaN if no comfort_range given)

        The DataFrame is sorted so that the design with the highest
        ``average_indoor_temperature`` (generally the best-performing
        design in a cold-climate heating scenario) appears first. For a
        cooling-dominated climate, re-sort on the metric that matters for
        that context instead.

    Raises:
        ValueError: if ``designs`` is empty.
        ThermalEngineValidationError: if any design label is invalid or
            any simulation input is invalid.
    """
    if not designs:
        raise ValueError("'designs' must contain at least one Shelter to compare.")

    rows = []
    for label, shelter in designs.items():
        validate_non_empty_string(label, "design label")
        if not isinstance(shelter, Shelter):
            raise TypeError(
                f"Design '{label}' must be a Shelter instance, got "
                f"{type(shelter).__name__}."
            )

        result = simulate_shelter(
            shelter=shelter,
            ambient_temperature=ambient_temperature,
            solar_radiation=solar_radiation,
            duration_hours=duration_hours,
            time_step_hours=time_step_hours,
            comfort_range=comfort_range,
        )
        s = result.summary
        rows.append(
            {
                "design": label,
                "shelter_name": shelter.name,
                "average_indoor_temperature": s["average_indoor_temperature"],
                "minimum_indoor_temperature": s["minimum_indoor_temperature"],
                "maximum_indoor_temperature": s["maximum_indoor_temperature"],
                "total_solar_energy_wh": s["total_solar_energy_wh"],
                "total_heat_loss_wh": s["total_heat_loss_wh"],
                "net_energy_balance_wh": s["net_energy_balance_wh"],
                "time_in_comfort_hours": s["time_in_comfort_hours"],
                "fraction_time_in_comfort": s["fraction_time_in_comfort"],
            }
        )

    df = pd.DataFrame(rows).set_index("design")
    df = df.sort_values("average_indoor_temperature", ascending=False)
    return df
