"""Abstract interface for climate data providers.

A real implementation might call NASA POWER, a national meteorological
API, or an internal weather-station dataset. The orchestrator only ever
depends on this interface.
"""
from abc import ABC, abstractmethod

from app.models.climate import ClimateProfile, ScenarioDefinition


class ClimateProvider(ABC):
    @abstractmethod
    def get_climate_profile(self, location: str, climate_description: str) -> ClimateProfile:
        """Return a ClimateProfile for the given location/description."""
        raise NotImplementedError

    @abstractmethod
    def get_scenarios(self, base_profile: ClimateProfile) -> list[ScenarioDefinition]:
        """Return a set of alternate environmental scenarios for robustness testing."""
        raise NotImplementedError
