from typing import Dict, List

from fastapi import HTTPException, status

from app.core.logging import logger
from app.models.material import Material
from app.models.simulation import Simulation, SimulationStatus
from app.repositories.memory_repository import RepositoryRegistry, new_id
from app.schemas.simulation import SimulationCreate
from app.services.design_service import DesignService
from app.services.climate_service import ClimateService
from app.services.material_service import MaterialService
from app.services.simulation_backend import (
    MockSimulationBackend,
    SimulationBackendUnavailableError,
)
from app.services.thermal_engine import MockThermalEngine, ThermalEngine


class SimulationService:
    def __init__(
        self,
        repos: RepositoryRegistry,
        design_service: DesignService,
        climate_service: ClimateService,
        material_service: MaterialService,
        thermal_engine: ThermalEngine = None,
    ):
        self.repos = repos
        self.design_service = design_service
        self.climate_service = climate_service
        self.material_service = material_service
        self.thermal_engine = thermal_engine or MockThermalEngine()
        self.backend = MockSimulationBackend()

    def _resolve_materials(self, design) -> Dict[str, Material]:
        return {
            "wall_material": self.material_service.get_material(design.wall_material),
            "roof_material": self.material_service.get_material(design.roof_material),
            "floor_material": self.material_service.get_material(design.floor_material),
            "insulation_material": self.material_service.get_material(design.insulation_material),
        }

    def create_simulation(self, payload: SimulationCreate) -> Simulation:
        if not self.repos.projects.exists(payload.project_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Project '{payload.project_id}' not found")
        self.design_service.get_design(payload.design_id)  # 404s if missing
        self.climate_service.get_climate(payload.climate_id)  # 404s if missing

        simulation = Simulation(
            id=new_id("sim"),
            project_id=payload.project_id,
            design_id=payload.design_id,
            climate_id=payload.climate_id,
            duration=payload.duration,
            timestep=payload.timestep,
            status=SimulationStatus.CREATED,
            backend=self.backend.name,
        )
        self.repos.simulations.add(simulation.id, simulation)
        logger.info("Created simulation %s for design %s", simulation.id, payload.design_id)
        return simulation

    def get_simulation(self, simulation_id: str) -> Simulation:
        simulation = self.repos.simulations.get(simulation_id)
        if simulation is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Simulation '{simulation_id}' not found")
        return simulation

    def run_simulation(self, simulation_id: str) -> Simulation:
        simulation = self.get_simulation(simulation_id)

        if not self.backend.is_available():
            simulation.status = SimulationStatus.FAILED
            simulation.error = "Simulation backend unavailable"
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Simulation backend unavailable",
            )

        simulation.status = SimulationStatus.RUNNING
        simulation.progress = 0.1
        logger.info("Running simulation %s", simulation_id)

        try:
            design = self.design_service.get_design(simulation.design_id)
            climate = self.climate_service.get_climate(simulation.climate_id)
            materials = self._resolve_materials(design)

            raw_results = self.thermal_engine.simulate(
                design, climate, materials, simulation.duration, simulation.timestep
            )
            simulation.results = self.thermal_engine.get_results(raw_results)
            simulation.status = SimulationStatus.COMPLETED
            simulation.progress = 1.0
            simulation.error = None
        except HTTPException:
            simulation.status = SimulationStatus.FAILED
            raise
        except Exception as exc:  # pragma: no cover - defensive
            simulation.status = SimulationStatus.FAILED
            simulation.error = str(exc)
            logger.error("Simulation %s failed: %s", simulation_id, exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Simulation failed: {exc}",
            )

        from datetime import datetime, timezone
        simulation.updated_at = datetime.now(timezone.utc)
        logger.info("Simulation %s completed", simulation_id)
        return simulation

    def get_results(self, simulation_id: str):
        simulation = self.get_simulation(simulation_id)
        if simulation.status != SimulationStatus.COMPLETED or simulation.results is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Simulation '{simulation_id}' has not completed successfully "
                f"(status={simulation.status.value})",
            )
        return simulation.results

    def list_simulations(self) -> List[Simulation]:
        return self.repos.simulations.list()
