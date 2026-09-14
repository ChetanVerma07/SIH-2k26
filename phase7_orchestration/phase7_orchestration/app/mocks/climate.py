"""Deterministic mock climate provider.

This does NOT call any external weather API. It derives a plausible,
deterministic ClimateProfile from keywords in the climate description
(e.g. "cold high-altitude", "hot arid", "tropical humid"). Values are
illustrative approximations for orchestration development only — see
README limitations.
"""
from app.interfaces.climate import ClimateProvider
from app.models.climate import ClimateProfile, ScenarioDefinition

# Keyword -> (avg, min, max outdoor temp C, avg solar W/m2, humidity %)
_CLIMATE_KEYWORDS: dict[str, tuple[float, float, float, float, float]] = {
    "cold high-altitude": (-5.0, -15.0, 5.0, 550.0, 25.0),
    "cold": (2.0, -8.0, 10.0, 350.0, 40.0),
    "hot arid": (32.0, 22.0, 42.0, 750.0, 15.0),
    "hot humid": (30.0, 24.0, 36.0, 500.0, 80.0),
    "tropical": (28.0, 23.0, 34.0, 480.0, 85.0),
    "temperate": (14.0, 6.0, 22.0, 400.0, 55.0),
}

_DEFAULT = (15.0, 5.0, 25.0, 400.0, 50.0)


class MockClimateProvider(ClimateProvider):
    def get_climate_profile(self, location: str, climate_description: str) -> ClimateProfile:
        desc = climate_description.lower().strip()
        missing: list[str] = []

        match = None
        for key, values in _CLIMATE_KEYWORDS.items():
            if key in desc:
                match = values
                break

        if match is None:
            match = _DEFAULT
            missing.append("climate_zone_lookup")

        avg_t, min_t, max_t, solar, humidity = match

        altitude = None
        if "high-altitude" in desc or "highland" in desc:
            altitude = 3500.0
        else:
            missing.append("altitude_m")

        return ClimateProfile(
            location=location,
            climate_zone=climate_description,
            avg_outdoor_temp_c=avg_t,
            min_outdoor_temp_c=min_t,
            max_outdoor_temp_c=max_t,
            avg_solar_radiation_wm2=solar,
            wind_speed_ms=4.0 if "high-altitude" in desc else 3.0,
            humidity_percent=humidity,
            altitude_m=altitude,
            data_points_available=24,
            missing_fields=missing,
            source="mock",
        )

    def get_scenarios(self, base_profile: ClimateProfile) -> list[ScenarioDefinition]:
        return [
            ScenarioDefinition(
                name="Cold + low solar radiation",
                description="Overcast cold conditions with minimal solar gain available",
                outdoor_temp_offset_c=-4.0,
                solar_radiation_factor=0.4,
            ),
            ScenarioDefinition(
                name="Cold + high solar radiation",
                description="Cold but clear conditions, typical of high-altitude winter days",
                outdoor_temp_offset_c=-2.0,
                solar_radiation_factor=1.3,
            ),
            ScenarioDefinition(
                name="Cloudy winter day",
                description="Reduced solar radiation with moderately cold temperatures",
                outdoor_temp_offset_c=-1.0,
                solar_radiation_factor=0.5,
            ),
            ScenarioDefinition(
                name="Clear winter day",
                description="Strong solar radiation with cold ambient temperature",
                outdoor_temp_offset_c=0.0,
                solar_radiation_factor=1.4,
            ),
            ScenarioDefinition(
                name="Warmer daytime condition",
                description="A milder daytime period, e.g. late spring transition",
                outdoor_temp_offset_c=8.0,
                solar_radiation_factor=1.1,
            ),
        ]
