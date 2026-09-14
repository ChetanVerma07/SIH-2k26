"""
Phase 8 - Simplified thermal model (independent of ANSYS).

A self-contained single-zone lumped-capacitance (RC network) model of the
shelter, solved with explicit Euler time-stepping over 24 hours. This is
NOT imported from any earlier phase -- Phase 8 must stand alone -- so the
"simplified model" referenced in the objectives is re-implemented here in
full, minimal but physically grounded.

Purpose: give the pipeline something fast and ANSYS-independent to
validate the (mock or real) ANSYS run against. Large deviation between
the two is exactly the kind of thing Phase 8's comparator/validator should
flag.
"""

from __future__ import annotations

import math

from config import ShelterDesignParams, ClimateParams, SimulationSettings
from core.results_importer import ThermalTimeSeries
from core.envelope_physics import envelope_ua, thermal_capacitance, solar_gain_params


def run_simplified_model(design: ShelterDesignParams,
                          climate: ClimateParams,
                          settings: SimulationSettings) -> ThermalTimeSeries:
    ua = envelope_ua(design)
    capacitance = thermal_capacitance(design)

    dt = settings.time_step_s
    n_steps = int(settings.duration_hours * 3600 / dt) + 1

    solar_absorptance, effective_solar_area = solar_gain_params(design)

    time_s, temps, flux = [], [], []
    indoor_temp = climate.ambient_temp_profile_c[0]

    for step in range(n_steps):
        t_s = step * dt
        t_h = t_s / 3600.0
        hour_idx = int(t_h) % 24
        next_idx = (hour_idx + 1) % 24
        frac = t_h - int(t_h)

        ambient = (climate.ambient_temp_profile_c[hour_idx] * (1 - frac)
                   + climate.ambient_temp_profile_c[next_idx] * frac)
        solar = (climate.solar_radiation_profile_w_m2[hour_idx] * (1 - frac)
                 + climate.solar_radiation_profile_w_m2[next_idx] * frac)

        q_solar = solar_absorptance * effective_solar_area * solar / design.wall_area_m2 \
            if design.wall_area_m2 else 0.0
        q_internal = design.internal_gains_w

        # Analytic (unconditionally stable) update for dT/dt = -(UA/C)*(T-Tamb) + (Qsolar+Qint)/C
        # over one timestep, holding ambient/solar/internal gains constant during dt.
        k = ua / capacitance
        t_equilibrium = ambient + (q_solar + q_internal) / ua if ua > 1e-9 else ambient
        indoor_temp = t_equilibrium + (indoor_temp - t_equilibrium) * math.exp(-k * dt)

        envelope_area = max(design.wall_area_m2 + design.roof_area_m2, 1.0)
        heat_flux = (ambient - indoor_temp) * ua / envelope_area

        time_s.append(t_s)
        temps.append(indoor_temp)
        flux.append(heat_flux)

    return ThermalTimeSeries(time_s=time_s, indoor_temp_c=temps, heat_flux_w_m2=flux)
