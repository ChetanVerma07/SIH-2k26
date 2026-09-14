from fastapi import APIRouter

from app.api.routes import (
    climate,
    comparisons,
    designs,
    health,
    materials,
    optimization,
    projects,
    recommendations,
    reports,
    simulations,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(projects.router)
api_router.include_router(designs.router)
api_router.include_router(climate.router)
api_router.include_router(materials.router)
api_router.include_router(simulations.router)
api_router.include_router(optimization.router)
api_router.include_router(recommendations.router)
api_router.include_router(comparisons.router)
api_router.include_router(reports.router)
