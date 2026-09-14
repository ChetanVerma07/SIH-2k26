"""
Climate / environmental condition model.

A ClimateCondition describes one day-type used to drive the simplified
thermal evaluator. Multiple ClimateConditions make up a "scenario set"
(analysis/scenarios.py) so a design's robustness can be checked across
several weather patterns rather than a single one.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ClimateCondition:
    name: str
    outdoor_temp_avg: float        # deg C, mean outdoor temperature over 24h
    outdoor_temp_amplitude: float  # deg C, half the day/night swing
    solar_irradiance_peak: float   # W/m2, peak solar irradiance at solar noon
    daylight_hours: float          # hours of daylight (irradiance > 0)
    wind_speed: float               # m/s, affects outer surface film resistance
    target_comfort_min: float = 18.0
    target_comfort_max: float = 26.0


# High-altitude cold-desert climate representative of Ladakh
LADAKH_WINTER = ClimateCondition(
    name="ladakh_winter_baseline",
    outdoor_temp_avg=-10.0,
    outdoor_temp_amplitude=8.0,
    solar_irradiance_peak=650.0,
    daylight_hours=9.0,
    wind_speed=4.0,
)

# Scenario set used for robustness / scenario-comparison analysis
SCENARIOS = {
    "cold_winter_day": ClimateCondition(
        name="cold_winter_day",
        outdoor_temp_avg=-12.0, outdoor_temp_amplitude=6.0,
        solar_irradiance_peak=400.0, daylight_hours=8.0, wind_speed=5.0,
    ),
    "cold_sunny_day": ClimateCondition(
        name="cold_sunny_day",
        outdoor_temp_avg=-8.0, outdoor_temp_amplitude=9.0,
        solar_irradiance_peak=750.0, daylight_hours=9.5, wind_speed=2.0,
    ),
    "cold_cloudy_day": ClimateCondition(
        name="cold_cloudy_day",
        outdoor_temp_avg=-9.0, outdoor_temp_amplitude=4.0,
        solar_irradiance_peak=180.0, daylight_hours=8.0, wind_speed=6.0,
    ),
    "summer_condition": ClimateCondition(
        name="summer_condition",
        outdoor_temp_avg=22.0, outdoor_temp_amplitude=8.0,
        solar_irradiance_peak=850.0, daylight_hours=13.0, wind_speed=3.0,
        target_comfort_min=20.0, target_comfort_max=28.0,
    ),
}
