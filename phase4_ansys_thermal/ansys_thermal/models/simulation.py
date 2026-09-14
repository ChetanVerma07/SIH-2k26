"""
Top-level simulation configuration model.

Bundles geometry, material assignment, and boundary conditions into a
single object that can be serialized, validated, passed to the ANSYS
adapter, and later called by a Python backend (e.g. a REST endpoint in
a future phase).
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional

from ansys_thermal.models.geometry import ShelterGeometry
from ansys_thermal.models.materials import MaterialAssignment
from ansys_thermal.models.climate import BoundaryConditions


@dataclass
class SimulationConfig:
    """A complete, self-contained description of one thermal
    simulation run."""

    name: str
    geometry: ShelterGeometry
    materials: MaterialAssignment
    boundary_conditions: BoundaryConditions

    analysis_type: str = "transient_thermal"
    notes: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "analysis_type": self.analysis_type,
            "notes": self.notes,
            "geometry": self.geometry.as_dict(),
            "materials": self.materials.as_dict(),
            "boundary_conditions": self.boundary_conditions.as_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationConfig":
        return cls(
            name=data["name"],
            analysis_type=data.get("analysis_type", "transient_thermal"),
            notes=data.get("notes"),
            geometry=ShelterGeometry.from_dict(data["geometry"]),
            materials=MaterialAssignment.from_dict(data["materials"]),
            boundary_conditions=BoundaryConditions.from_dict(data["boundary_conditions"]),
        )
