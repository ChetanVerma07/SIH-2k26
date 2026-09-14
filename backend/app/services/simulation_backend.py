"""
SimulationBackend abstraction.

Represents WHERE the actual number-crunching happens. In this phase only
the mock backend is functional. The ANSYS backend is a real class with a
real interface, but clearly reports itself as not configured -- it never
fabricates ANSYS-quality output.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class SimulationBackendUnavailableError(Exception):
    """Raised when a simulation backend cannot service a request."""


class SimulationBackend(ABC):
    name: str = "base"

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


class MockSimulationBackend(SimulationBackend):
    name = "MOCK"

    def is_available(self) -> bool:
        return True

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Delegates to the ThermalEngine via the caller; this class exists
        # to model the "backend selection" seam described in the architecture.
        return payload


class ANSYSSimulationBackend(SimulationBackend):
    name = "ANSYS"

    def is_available(self) -> bool:
        return False

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise SimulationBackendUnavailableError("ANSYS backend not configured")
