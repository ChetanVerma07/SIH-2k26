"""Abstract interface for design candidate generation / optimization.

A real implementation might use a genetic algorithm, Bayesian optimization,
or an ML-driven generative design search. The orchestrator only ever
depends on this interface.
"""
from abc import ABC, abstractmethod

from app.models.climate import ClimateProfile
from app.models.design import ShelterDesign
from app.models.request import ShelterDesignRequest


class DesignOptimizer(ABC):
    @abstractmethod
    def generate_candidates(
        self, request: ShelterDesignRequest, climate: ClimateProfile
    ) -> list[ShelterDesign]:
        """Generate a set of candidate shelter designs for evaluation."""
        raise NotImplementedError

    @abstractmethod
    def generate_baseline(
        self, request: ShelterDesignRequest, climate: ClimateProfile
    ) -> ShelterDesign:
        """Generate a conventional/simple baseline design for comparison."""
        raise NotImplementedError
