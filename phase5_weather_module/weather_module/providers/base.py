"""Abstract WeatherProvider interface.

Any concrete weather data source (mock, or a real API adapter) must
implement this interface. The rest of the application only depends on
this abstraction, so providers can be swapped without touching
downstream code (normalization, validation, simulation export, API).
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import List, Optional

from weather_module.models.location import Location
from weather_module.models.weather import WeatherObservation


class ProviderError(Exception):
    """Base error for provider failures (network, parsing, etc.)."""


class ProviderUnavailableError(ProviderError):
    """The provider could not be reached (network/timeout/HTTP error)."""


class InvalidLocationError(ProviderError):
    """The location could not be resolved by this provider."""


class NoHistoricalDataError(ProviderError):
    """No historical data is available for the requested date(s)."""


class WeatherProvider(ABC):
    """Abstract base class for all weather data providers."""

    name: str = "abstract"

    @abstractmethod
    def get_current_weather(self, location: Location) -> WeatherObservation:
        """Return the current weather observation for a location."""
        raise NotImplementedError

    @abstractmethod
    def get_forecast(
        self, location: Location, hours: int = 24, interval_minutes: int = 60
    ) -> List[WeatherObservation]:
        """Return a forecast time series for the given horizon and interval."""
        raise NotImplementedError

    @abstractmethod
    def get_historical_weather(
        self,
        location: Location,
        start: date,
        end: Optional[date] = None,
    ) -> List[WeatherObservation]:
        """Return historical observations for a date or date range (inclusive)."""
        raise NotImplementedError

    def resolve_location(self, location: Location) -> Location:
        """Optionally convert a name-based location into coordinates.

        Default implementation requires coordinates already be present;
        providers with geocoding support should override this.
        """
        if not location.has_coordinates():
            raise InvalidLocationError(
                f"{self.name} provider cannot geocode '{location.name}'; "
                "please supply latitude/longitude directly."
            )
        return location
