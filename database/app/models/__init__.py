"""
Import every model so that Base.metadata is fully populated for both
Alembic autogenerate and `Base.metadata.create_all` in tests.
"""
from app.core.database import Base  # noqa: F401

from app.models.project import Project  # noqa: F401
from app.models.material import Material, MaterialCategory  # noqa: F401
from app.models.climate import ClimateProfile, ClimateData  # noqa: F401
from app.models.design import Design  # noqa: F401
from app.models.simulation import Simulation, SimulationStatus, SimulationBackend  # noqa: F401
from app.models.simulation_result import SimulationResult  # noqa: F401
from app.models.optimization import OptimizationRun, OptimizationStatus  # noqa: F401
from app.models.optimization_candidate import OptimizationCandidate  # noqa: F401
from app.models.recommendation import Recommendation  # noqa: F401
from app.models.report import Report, ReportFormat  # noqa: F401

__all__ = [
    "Base",
    "Project",
    "Material",
    "MaterialCategory",
    "ClimateProfile",
    "ClimateData",
    "Design",
    "Simulation",
    "SimulationStatus",
    "SimulationBackend",
    "SimulationResult",
    "OptimizationRun",
    "OptimizationStatus",
    "OptimizationCandidate",
    "Recommendation",
    "Report",
    "ReportFormat",
]
