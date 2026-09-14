"""MockWeatherProvider: deterministic, offline weather data.

Works without any API key or network access. Used for:
  - development and testing without internet access
  - the Ladakh / high-altitude cold-region demo preset
  - fallback when a live provider is unavailable

All values are clearly labeled DataSource.MOCK and, where solar
radiation is synthesized rather than looked up from a fixed table,
DataSource.ESTIMATED.
"""
from __future__ import annotations
import math
import random
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from weather_module.models.location import Location
from weather_module.models.weather import WeatherObservation, DataSource, QualityFlag
from weather_module.processing.solar import estimate_solar_radiation_wm2
from weather_module.providers.base import WeatherProvider

# Built-in named presets: name -> (lat, lon, elevation_m, mean_temp_c, temp_amplitude_c,
#                                   mean_pressure_hpa, mean_humidity_pct, mean_wind_ms)
PRESETS = {
    "ladakh": dict(
        latitude=34.1526, longitude=77.5771, elevation_m=3500,
        mean_temp_c=-8.0, temp_amplitude_c=12.0,
        mean_pressure_hpa=650.0, mean_humidity_pct=32.0,
        mean_wind_ms=3.5, cloud_cover_pct=10.0,
    ),
    "delhi": dict(
        latitude=28.6139, longitude=77.2090, elevation_m=216,
        mean_temp_c=28.0, temp_amplitude_c=8.0,
        mean_pressure_hpa=1005.0, mean_humidity_pct=55.0,
        mean_wind_ms=2.2, cloud_cover_pct=30.0,
    ),
    "mumbai": dict(
        latitude=19.0760, longitude=72.8777, elevation_m=14,
        mean_temp_c=29.0, temp_amplitude_c=4.0,
        mean_pressure_hpa=1010.0, mean_humidity_pct=75.0,
        mean_wind_ms=3.0, cloud_cover_pct=45.0,
    ),
}

DEFAULT_PRESET = "delhi"


class MockWeatherProvider(WeatherProvider):
    """Deterministic offline weather provider using a diurnal sinusoidal model.

    Deterministic: given the same location + timestamp, output is identical
    across runs (seeded by date + rounded coordinates), so tests and demos
    are reproducible.
    """

    name = "mock"

    def __init__(self, preset: str = DEFAULT_PRESET):
        self.preset_key = preset.lower() if preset else DEFAULT_PRESET
        self.preset = PRESETS.get(self.preset_key, PRESETS[DEFAULT_PRESET])

    # ------------------------------------------------------------------
    def resolve_location(self, location: Location) -> Location:
        """The mock provider can 'geocode' known preset names; otherwise
        it requires explicit coordinates."""
        if location.has_coordinates():
            return location
        key = (location.name or "").strip().lower()
        if key in PRESETS:
            p = PRESETS[key]
            return Location(
                name=location.name, latitude=p["latitude"], longitude=p["longitude"],
                elevation_m=p["elevation_m"],
            )
        raise ValueError(
            f"MockWeatherProvider cannot resolve location '{location.name}'. "
            f"Known presets: {list(PRESETS.keys())}. Supply latitude/longitude directly "
            "for other locations."
        )

    def _preset_for(self, location: Location) -> dict:
        key = (location.name or "").strip().lower()
        return PRESETS.get(key, self.preset)

    def _rng_for(self, location: Location, dt: datetime) -> random.Random:
        seed = f"{round(location.latitude, 2)}:{round(location.longitude, 2)}:{dt.date().isoformat()}"
        return random.Random(seed)

    def _synth_observation(self, location: Location, dt: datetime) -> WeatherObservation:
        p = self._preset_for(location)
        rng = self._rng_for(location, dt)

        hour_frac = dt.hour + dt.minute / 60.0
        # Diurnal temperature cycle, coldest ~05:00, warmest ~15:00
        phase = (hour_frac - 15.0) / 24.0 * 2 * math.pi
        temp = p["mean_temp_c"] - p["temp_amplitude_c"] * math.cos(phase)
        temp += rng.uniform(-0.5, 0.5)

        cloud_cover = max(0.0, min(100.0, p["cloud_cover_pct"] + rng.uniform(-10, 10)))
        humidity = max(0.0, min(100.0, p["mean_humidity_pct"] + rng.uniform(-5, 5)
                                 + 0.15 * cloud_cover))
        pressure = p["mean_pressure_hpa"] + rng.uniform(-1.5, 1.5)
        wind = max(0.0, p["mean_wind_ms"] + rng.uniform(-1.0, 1.0))
        wind_dir = rng.uniform(0, 360)
        precip = 0.0 if cloud_cover < 60 else round(rng.uniform(0, 2.5), 2)

        solar = estimate_solar_radiation_wm2(
            dt, location.latitude, location.longitude, cloud_cover_pct=cloud_cover
        )

        return WeatherObservation(
            timestamp=dt,
            latitude=location.latitude,
            longitude=location.longitude,
            location_name=location.name or self.preset_key.title(),
            temperature_c=round(temp, 2),
            humidity_pct=round(humidity, 2),
            pressure_hpa=round(pressure, 2),
            solar_radiation_wm2=solar,
            wind_speed_ms=round(wind, 2),
            wind_direction_deg=round(wind_dir, 1),
            cloud_cover_pct=round(cloud_cover, 1),
            precipitation_mm=precip,
            solar_radiation_source=DataSource.ESTIMATED,
            data_source=DataSource.MOCK,
            quality=QualityFlag.VALID,
        )

    # ------------------------------------------------------------------
    def get_current_weather(self, location: Location) -> WeatherObservation:
        location = self.resolve_location(location)
        now = datetime.now(timezone.utc).replace(microsecond=0)
        return self._synth_observation(location, now)

    def get_forecast(
        self, location: Location, hours: int = 24, interval_minutes: int = 60
    ) -> List[WeatherObservation]:
        location = self.resolve_location(location)
        start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        n_steps = int((hours * 60) / interval_minutes)
        obs = []
        for i in range(n_steps):
            dt = start + timedelta(minutes=i * interval_minutes)
            o = self._synth_observation(location, dt)
            o.data_source = DataSource.MOCK  # forecast values are also mock-synthesized here
            obs.append(o)
        return obs

    def get_historical_weather(
        self, location: Location, start: date, end: Optional[date] = None
    ) -> List[WeatherObservation]:
        location = self.resolve_location(location)
        end = end or start
        if end < start:
            raise ValueError("end date must not be before start date")
        obs = []
        current = start
        while current <= end:
            for hour in range(24):
                dt = datetime(current.year, current.month, current.day, hour, tzinfo=timezone.utc)
                obs.append(self._synth_observation(location, dt))
            current += timedelta(days=1)
        return obs

    # ------------------------------------------------------------------
    def get_demo_profile_24h(self, preset: str = "ladakh", interval_minutes: int = 60):
        """Convenience method for the Ladakh / high-altitude demo preset."""
        p = PRESETS.get(preset.lower(), PRESETS["ladakh"])
        location = Location(
            name=preset.title(), latitude=p["latitude"], longitude=p["longitude"],
            elevation_m=p["elevation_m"],
        )
        start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        n_steps = int((24 * 60) / interval_minutes)
        obs = []
        for i in range(n_steps):
            dt = start + timedelta(minutes=i * interval_minutes)
            obs.append(self._synth_observation(location, dt))
        return obs, location
