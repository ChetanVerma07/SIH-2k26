"""
Phase 8 - SimulationBackend abstraction.

Every concrete backend (Mock, ANSYS, or a future FEA tool) implements this
same interface, so the rest of the pipeline never needs to know which
engine actually produced the numbers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RunStatus(str, Enum):
    NOT_STARTED = "not_started"
    INPUT_READY = "input_ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BackendRunResult:
    status: RunStatus
    results_file: Optional[str] = None
    raw_log: str = ""
    error_message: Optional[str] = None
    wall_clock_s: float = 0.0


class SimulationBackend(ABC):
    """Abstract interface implemented by MockANSYSBackend and ANSYSBackend."""

    name: str = "abstract"

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this backend can actually execute a simulation
        in the current environment (e.g. ANSYS binary + license found)."""
        raise NotImplementedError

    @abstractmethod
    def prepare_input(self, case_dir: str, design, climate, settings) -> str:
        """Generate the backend-specific input file(s) for the case and
        return the path to the primary input file."""
        raise NotImplementedError

    @abstractmethod
    def run(self, case_dir: str, input_file: str, settings) -> BackendRunResult:
        """Execute (or simulate executing) the analysis and return a
        BackendRunResult pointing at the results file."""
        raise NotImplementedError

    def get_backend_info(self) -> dict:
        return {
            "name": self.name,
            "available": self.is_available(),
        }
