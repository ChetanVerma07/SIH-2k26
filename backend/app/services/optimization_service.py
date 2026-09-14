from datetime import datetime, timezone
from typing import List

from fastapi import HTTPException, status

from app.core.logging import logger
from app.models.optimization import Optimization, OptimizationStatus
from app.repositories.memory_repository import RepositoryRegistry, new_id
from app.schemas.optimization import OptimizationCreate
from app.services.design_service import DesignService
from app.services.climate_service import ClimateService
from app.services.material_service import MaterialService
from app.services.optimization_engine import MockOptimizationEngine, OptimizationEngine
from app.services.thermal_engine import MockThermalEngine


class OptimizationService:
    def __init__(
        self,
        repos: RepositoryRegistry,
        design_service: DesignService,
        climate_service: ClimateService,
        material_service: MaterialService,
        engine: OptimizationEngine = None,
    ):
        self.repos = repos
        self.design_service = design_service
        self.climate_service = climate_service
        self.material_service = material_service
        self.engine = engine or MockOptimizationEngine(MockThermalEngine())

    def create_optimization(self, payload: OptimizationCreate) -> Optimization:
        if not self.repos.projects.exists(payload.project_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Project '{payload.project_id}' not found")
        self.design_service.get_design(payload.baseline_design_id)  # 404s if missing

        optimization = Optimization(
            id=new_id("opt"),
            project_id=payload.project_id,
            baseline_design_id=payload.baseline_design_id,
            parameters=payload.parameters.model_dump(),
            status=OptimizationStatus.CREATED,
        )
        self.repos.optimizations.add(optimization.id, optimization)
        logger.info("Created optimization %s", optimization.id)
        return optimization

    def get_optimization(self, optimization_id: str) -> Optimization:
        optimization = self.repos.optimizations.get(optimization_id)
        if optimization is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Optimization '{optimization_id}' not found")
        return optimization

    def run_optimization(self, optimization_id: str, climate_location: str = "Composite") -> Optimization:
        optimization = self.get_optimization(optimization_id)
        optimization.status = OptimizationStatus.RUNNING
        logger.info("Running optimization %s", optimization_id)

        try:
            baseline_design = self.design_service.get_design(optimization.baseline_design_id)
            climate = self.climate_service.get_by_location(climate_location)

            candidate_pairs = self.engine.generate_candidates(baseline_design, optimization.parameters)

            materials_cache = {}

            def resolve_materials(design):
                key = (design.wall_material, design.roof_material, design.floor_material, design.insulation_material)
                if key not in materials_cache:
                    materials_cache[key] = {
                        "wall_material": self.material_service.get_material(design.wall_material),
                        "roof_material": self.material_service.get_material(design.roof_material),
                        "floor_material": self.material_service.get_material(design.floor_material),
                        "insulation_material": self.material_service.get_material(design.insulation_material),
                    }
                return materials_cache[key]

            candidates = []
            for candidate_design, modifications in candidate_pairs:
                candidate_design.id = new_id("design")
                candidate_design.project_id = optimization.project_id
                self.repos.designs.add(candidate_design.id, candidate_design)

                materials = resolve_materials(candidate_design)
                scored = self.engine.score(
                    candidate_design,
                    climate,
                    materials,
                    optimization.parameters.get("target_metric", "comfort_percentage"),
                )
                scored.modifications = modifications
                candidates.append(scored)

            candidates.sort(key=lambda c: c.score, reverse=True)
            optimization.candidates = candidates
            optimization.best_candidate_design_id = candidates[0].design_id if candidates else None
            optimization.status = OptimizationStatus.COMPLETED
            optimization.error = None
        except HTTPException:
            optimization.status = OptimizationStatus.FAILED
            raise
        except Exception as exc:  # pragma: no cover - defensive
            optimization.status = OptimizationStatus.FAILED
            optimization.error = str(exc)
            logger.error("Optimization %s failed: %s", optimization_id, exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Optimization failed: {exc}",
            )

        optimization.updated_at = datetime.now(timezone.utc)
        logger.info("Optimization %s completed with %d candidates", optimization_id, len(optimization.candidates))
        return optimization

    def list_optimizations(self) -> List[Optimization]:
        return self.repos.optimizations.list()
