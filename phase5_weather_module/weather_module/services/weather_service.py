"""WeatherService: orchestration layer.

Ties together a WeatherProvider, validation, resampling, and simulation
profile generation. This is the main entry point the rest of an
application (and the FastAPI layer) should use — it never exposes
provider-specific data structures, only normalized WeatherObservation /
dict output.
"""
from __future__ import annotations
from datetime import date, datetime
from typing import List, Optional

from weather_module.models.location import Location
from weather_module.models.weather import WeatherObservation
from weather_module.processing.resampler import resample
from weather_module.processing.validator import validate_series, validate_single, QualityStats
from weather_module.providers.base import (
    WeatherProvider, ProviderError, ProviderUnavailableError, InvalidLocationError,
)
from weather_module.providers.mock import MockWeatherProvider


class WeatherService:
    """High-level facade over a WeatherProvider (or providers)."""

    def __init__(
        self,
        provider: Optional[WeatherProvider] = None,
        fallback_provider: Optional[WeatherProvider] = None,
    ):
        self.provider = provider or MockWeatherProvider()
        # If a live provider fails, we can optionally fall back to mock data —
        # but the resulting observations are always clearly labeled as MOCK,
        # never silently presented as live/measured data.
        self.fallback_provider = fallback_provider

    # ------------------------------------------------------------------
    def _with_fallback(self, fn_name: str, *args, **kwargs):
        try:
            fn = getattr(self.provider, fn_name)
            return fn(*args, **kwargs), self.provider.name
        except ProviderError:
            if self.fallback_provider is None:
                raise
            fn = getattr(self.fallback_provider, fn_name)
            return fn(*args, **kwargs), self.fallback_provider.name

    def get_current(self, location: Location) -> WeatherObservation:
        obs, source_name = self._with_fallback("get_current_weather", location)
        validate_single(obs)
        return obs

    def get_forecast(
        self, location: Location, hours: int = 24, interval_minutes: int = 60
    ) -> List[WeatherObservation]:
        obs, _ = self._with_fallback(
            "get_forecast", location, hours=hours, interval_minutes=interval_minutes
        )
        validate_series(obs)
        return obs

    def get_historical(
        self, location: Location, start: date, end: Optional[date] = None
    ) -> List[WeatherObservation]:
        obs, _ = self._with_fallback("get_historical_weather", location, start=start, end=end)
        validate_series(obs)
        return obs

    # ------------------------------------------------------------------
    def generate_climate_profile(
        self,
        location: Location,
        duration_hours: int = 24,
        interval_minutes: int = 60,
        use_forecast: bool = True,
    ) -> List[WeatherObservation]:
        """Build a simulation-ready time series at the requested interval.

        Pulls a forecast series then resamples to the exact requested
        interval, validating throughout.
        """
        raw = self.get_forecast(location, hours=duration_hours, interval_minutes=min(interval_minutes, 60) or 60)
        series = resample(raw, interval_minutes)
        validate_series(series)
        return series

    def generate_simulation_profile(
        self,
        location: Location,
        duration_hours: int = 24,
        interval_minutes: int = 60,
    ) -> dict:
        """Return a dict ready to hand to a thermal simulation engine."""
        series = self.generate_climate_profile(location, duration_hours, interval_minutes)
        stats = validate_series(series)
        return {
            "location": location.display_name(),
            "latitude": location.latitude,
            "longitude": location.longitude,
            "duration_hours": duration_hours,
            "interval_minutes": interval_minutes,
            "provider": self.provider.name,
            "quality_summary": stats.to_dict(),
            "observations": [o.to_dict() for o in series],
        }

    def demo_ladakh_profile(self, interval_minutes: int = 60) -> dict:
        """Offline demo profile using the built-in Ladakh preset. No API key required."""
        provider = self.provider if isinstance(self.provider, MockWeatherProvider) else MockWeatherProvider()
        obs, location = provider.get_demo_profile_24h(preset="ladakh", interval_minutes=interval_minutes)
        stats = validate_series(obs)
        return {
            "location": "Ladakh (DEMO / MOCK DATA)",
            "latitude": location.latitude,
            "longitude": location.longitude,
            "elevation_m": location.elevation_m,
            "duration_hours": 24,
            "interval_minutes": interval_minutes,
            "provider": "mock",
            "data_label": "DEMO / MOCK DATA",
            "quality_summary": stats.to_dict(),
            "observations": [o.to_dict() for o in obs],
        }
