"""Abstract interface for high-fidelity structural/thermal validation.

A real implementation would drive ANSYS (or another FEA/CFD tool) via its
scripting API or batch job submission. The orchestrator only ever depends
on this interface, and must never assume the underlying implementation is
real ANSYS software.
"""
from abc import ABC, abstractmethod

from app.models.design import ShelterDesign
from app.models.results import ANSYSValidationResult


class ANSYSValidator(ABC):
    @abstractmethod
    def validate_design(self, design: ShelterDesign) -> str:
        """Kick off validation for a design and return a job/reference id."""
        raise NotImplementedError

    @abstractmethod
    def get_validation_results(self, job_id: str, design: ShelterDesign) -> ANSYSValidationResult:
        """Retrieve validation results for a previously submitted job."""
        raise NotImplementedError
