"""
FastThermalEvaluator: a lightweight, deterministic, quasi-steady-state
thermal model. This is NOT a replacement for ANSYS — it is a fast,
explainable stand-in that responds in the *physically correct
direction* to every design change, which is exactly what the
optimizer needs to search intelligently.

Model summary (documented so results are explainable):

1. Envelope conductance (U*A, in W/K) is computed for walls, roof,
   floor, windows/openings and door using a series-resistance model:
       R_total = R_si + sum(thickness_i / conductivity_i) + R_se
       U = 1 / R_total
   Windows use a fixed double-glazing U-value (spec-level assumption).

2. A 24-hour outdoor temperature profile is generated as a cosine wave
   around `outdoor_temp_avg` with amplitude `outdoor_temp_amplitude`,
   coldest at 05:00 and warmest at 15:00.

3. A triangular solar irradiance profile is generated over the
   daylight hours, peaking at solar noon at `solar_irradiance_peak`.
   Effective irradiance on the opening is scaled by an orientation
   factor: openings facing the "equator direction" (orientation = 0)
   receive full irradiance; the factor falls off with |orientation|
   using a cosine law, floored at 0.15 so no orientation is ever fully
   blind to diffuse radiation.

4. For every hour:
     solar_gain_W   = irradiance_eff * opening_area * glazing_transmittance
                       + irradiance_eff * wall_area * wall_absorptivity * 0.04
                       (small opaque-wall solar-absorption term)
     passive_indoor  = outdoor_temp + solar_gain_W / UA_total
     (quasi-steady energy balance — thermal mass / time-lag are
     explicitly NOT modeled in this prototype; see README limitations)
     heat_loss_W    = UA_total * (passive_indoor - outdoor_temp)
                       [equals solar_gain_W under this steady balance,
                       i.e. all solar gain that raises indoor temp is
                       balanced by extra envelope loss — documented
                       simplification]
     heating_W      = UA_total * (comfort_min - passive_indoor)
                       if passive_indoor < comfort_min else 0

5. Daily totals are integrated (Wh -> kWh) and comfort_percentage is
   the fraction of the 24 hours where passive_indoor lies within
   [comfort_min, comfort_max].
"""

import math
from optimizer.models.materials import get_material
from optimizer.thermal.evaluator import ThermalEvaluator

# Surface film resistances (m2K/W) - typical values
R_SI = 0.13   # internal surface resistance
R_SE = 0.04   # external surface resistance (increases slightly with wind, see below)

WINDOW_U_VALUE = 2.8     # W/m2K, typical double glazing
DOOR_U_VALUE = 2.0       # W/m2K, insulated door
GLAZING_TRANSMITTANCE = 0.75  # fraction of solar radiation transmitted through glazing


def _layer_resistance(thickness_m: float, conductivity: float) -> float:
    conductivity = max(conductivity, 1e-6)
    return thickness_m / conductivity


def _element_u_value(thickness_m: float, material_name: str,
                      insulation_thickness_m: float, insulation_material_name: str,
                      wind_speed: float) -> float:
    """U-value (W/m2K) of a wall/roof/floor element = base material layer
    in series with the insulation layer, plus surface films."""
    mat = get_material(material_name)
    ins = get_material(insulation_material_name)
    r_se = R_SE + max(0.0, (wind_speed - 2.0)) * 0.005  # more wind -> slightly lower r_se
    r_total = (
        R_SI
        + _layer_resistance(thickness_m, mat.conductivity)
        + _layer_resistance(insulation_thickness_m, ins.conductivity)
        + r_se
    )
    return 1.0 / r_total


def _orientation_factor(orientation_deg: float) -> float:
    rad = math.radians(orientation_deg % 360)
    factor = math.cos(rad)
    return max(factor, 0.15)


class FastThermalEvaluator(ThermalEvaluator):
    """Default, ANSYS-free implementation of ThermalEvaluator used by all
    optimization algorithms in this phase."""

    def __init__(self, hours_per_day: int = 24):
        self.hours_per_day = hours_per_day

    def evaluate(self, design, climate) -> dict:
        wall_u = _element_u_value(design.wall_thickness, design.wall_material,
                                   design.insulation_thickness, design.insulation_material,
                                   climate.wind_speed)
        roof_u = _element_u_value(design.roof_thickness, design.roof_material,
                                   design.insulation_thickness, design.insulation_material,
                                   climate.wind_speed)
        floor_u = _element_u_value(design.floor_thickness, design.floor_material,
                                    design.insulation_thickness, design.insulation_material,
                                    climate.wind_speed * 0.2)  # floor sheltered from wind

        wall_area = design.net_wall_area()
        roof_area = design.floor_area()
        floor_area = design.floor_area()

        ua_total = (
            wall_u * wall_area
            + roof_u * roof_area
            + floor_u * floor_area
            + WINDOW_U_VALUE * design.opening_area
            + DOOR_U_VALUE * design.door_area
        )
        ua_total = max(ua_total, 1e-3)

        wall_mat = get_material(design.wall_material)
        orient_factor = _orientation_factor(design.orientation)

        hourly_indoor = []
        hourly_outdoor = []
        hourly_solar_w = []
        hourly_heatloss_w = []
        hourly_heating_w = []

        in_comfort_hours = 0
        n = self.hours_per_day

        for h in range(n):
            hour_frac = h / n * 24.0
            outdoor_t = climate.outdoor_temp_avg + climate.outdoor_temp_amplitude * math.cos(
                math.radians((hour_frac - 15.0) * 15.0)
            )

            solar_start = 12.0 - climate.daylight_hours / 2.0
            solar_end = 12.0 + climate.daylight_hours / 2.0
            if solar_start <= hour_frac <= solar_end:
                half = climate.daylight_hours / 2.0
                dist_from_noon = abs(hour_frac - 12.0)
                irradiance = climate.solar_irradiance_peak * max(0.0, 1.0 - dist_from_noon / half)
            else:
                irradiance = 0.0

            irradiance_eff = irradiance * orient_factor

            solar_w = (
                irradiance_eff * design.opening_area * GLAZING_TRANSMITTANCE
                + irradiance_eff * wall_area * wall_mat.solar_absorptivity * 0.04
            )

            passive_indoor = outdoor_t + solar_w / ua_total

            comfort_min = climate.target_comfort_min
            comfort_max = climate.target_comfort_max
            heating_w = ua_total * max(comfort_min - passive_indoor, 0.0)

            # "Real" heat loss is evaluated against the *managed* indoor
            # temperature (passive temperature, topped up to comfort_min
            # by heating when needed). This is what makes insulation
            # reduce heat loss during the (majority of) hours where
            # backup heating is required - during purely solar-driven
            # hours, loss = solar input by energy-balance construction,
            # independent of UA (see module docstring / README limitations).
            managed_indoor = max(passive_indoor, comfort_min)
            heat_loss_w = ua_total * max(managed_indoor - outdoor_t, 0.0)

            if comfort_min <= passive_indoor <= comfort_max:
                in_comfort_hours += 1

            hourly_indoor.append(passive_indoor)
            hourly_outdoor.append(outdoor_t)
            hourly_solar_w.append(solar_w)
            hourly_heatloss_w.append(heat_loss_w)
            hourly_heating_w.append(heating_w)

        dt_hours = 24.0 / n
        total_solar_kwh = sum(hourly_solar_w) * dt_hours / 1000.0
        total_heatloss_kwh = sum(hourly_heatloss_w) * dt_hours / 1000.0
        total_heating_kwh = sum(hourly_heating_w) * dt_hours / 1000.0
        comfort_pct = in_comfort_hours / n * 100.0

        return {
            "avg_indoor_temp_c": sum(hourly_indoor) / n,
            "min_indoor_temp_c": min(hourly_indoor),
            "max_indoor_temp_c": max(hourly_indoor),
            "comfort_percentage": comfort_pct,
            "total_heat_loss_kwh": total_heatloss_kwh,
            "total_solar_gain_kwh": total_solar_kwh,
            "heating_requirement_kwh": total_heating_kwh,
            "hourly_indoor_temp": hourly_indoor,
            "hourly_outdoor_temp": hourly_outdoor,
            "ua_total_w_per_k": ua_total,
            "wall_u_value": wall_u,
            "roof_u_value": roof_u,
            "floor_u_value": floor_u,
        }
