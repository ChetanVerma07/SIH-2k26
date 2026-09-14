"""
Dependency providers.

FastAPI routes depend on these functions to obtain service instances.
Services are constructed on top of a single shared RepositoryRegistry so
that data created via one route is visible to others within the same
process (simulating persistent storage without a real database).
"""
from functools import lru_cache

from app.repositories.memory_repository import RepositoryRegistry, repository_registry
from app.services.climate_service import ClimateService
from app.services.comparison_service import ComparisonService
from app.services.design_service import DesignService
from app.services.material_service import MaterialService
from app.services.optimization_service import OptimizationService
from app.services.project_service import ProjectService
from app.services.recommendation_service import RecommendationService
from app.services.report_service import ReportService
from app.services.simulation_service import SimulationService


def get_repos() -> RepositoryRegistry:
    return repository_registry


@lru_cache()
def get_material_service() -> MaterialService:
    return MaterialService(get_repos())


@lru_cache()
def get_climate_service() -> ClimateService:
    return ClimateService(get_repos())


@lru_cache()
def get_project_service() -> ProjectService:
    return ProjectService(get_repos())


@lru_cache()
def get_design_service() -> DesignService:
    return DesignService(get_repos())


@lru_cache()
def get_simulation_service() -> SimulationService:
    return SimulationService(
        get_repos(),
        get_design_service(),
        get_climate_service(),
        get_material_service(),
    )


@lru_cache()
def get_optimization_service() -> OptimizationService:
    return OptimizationService(
        get_repos(),
        get_design_service(),
        get_climate_service(),
        get_material_service(),
    )


@lru_cache()
def get_comparison_service() -> ComparisonService:
    return ComparisonService(
        get_design_service(),
        get_climate_service(),
        get_material_service(),
    )


@lru_cache()
def get_recommendation_service() -> RecommendationService:
    return RecommendationService(
        get_project_service(),
        get_design_service(),
        get_climate_service(),
        get_material_service(),
    )


@lru_cache()
def get_report_service() -> ReportService:
    return ReportService(
        get_project_service(),
        get_design_service(),
        get_climate_service(),
        get_material_service(),
        get_recommendation_service(),
        get_comparison_service(),
    )
