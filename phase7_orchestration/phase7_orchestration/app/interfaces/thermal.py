"""Abstract interface for thermal simulation engines.

A real implementation might wrap EnergyPlus, a custom RC-network thermal
model, or a machine-learned surrogate. The orchestrator only ever depends
on this interface.
"""
from abc import ABC, abstractmethod

from app.models.climate import ClimateProfile
from app.models.design import ShelterDesign
from app.models.request import ComfortRange
from app.models.results import ThermalPerformance


class ThermalSimulator(ABC):
    @abstractmethod
    def simulate(
        self,
        design: ShelterDesign,
        climate: ClimateProfile,
        comfort_range: ComfortRange,
        duration_hours: int,
        outdoor_temp_offset_c: float = 0.0,
        solar_radiation_factor: float = 1.0,
    ) -> ThermalPerformance:
        """Run a thermal simulation for one design under one climate profile.

        outdoor_temp_offset_c and solar_radiation_factor allow the same
        base climate profile to be perturbed for scenario/robustness
        analysis without needing a new ClimateProvider call.
        """
        raise NotImplementedError
