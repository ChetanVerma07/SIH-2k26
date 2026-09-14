from typing import List

from fastapi import HTTPException, status

from app.core.logging import logger
from app.schemas.recommendation import ComparisonMetric, ComparisonResponse
from app.services.climate_service import ClimateService
from app.services.design_service import DesignService
from app.services.material_service import MaterialService
from app.services.thermal_engine import MockThermalEngine, ThermalEngine


class ComparisonService:
    def __init__(
        self,
        design_service: DesignService,
        climate_service: ClimateService,
        material_service: MaterialService,
        thermal_engine: ThermalEngine = None,
    ):
        self.design_service = design_service
        self.climate_service = climate_service
        self.material_service = material_service
        self.thermal_engine = thermal_engine or MockThermalEngine()

    def compare(self, design_ids: List[str], climate_location: str = "Composite") -> ComparisonResponse:
        if len(design_ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least two design_ids are required for comparison",
            )

        climate = self.climate_service.get_by_location(climate_location)

        metrics: List[ComparisonMetric] = []
        for design_id in design_ids:
            design = self.design_service.get_design(design_id)
            materials = {
                "wall_material": self.material_service.get_material(design.wall_material),
                "roof_material": self.material_service.get_material(design.roof_material),
                "floor_material": self.material_service.get_material(design.floor_material),
                "insulation_material": self.material_service.get_material(design.insulation_material),
            }
            raw = self.thermal_engine.simulate(design, climate, materials, duration=24, timestep=1)

            energy_requirement = round(max(raw["total_heat_loss"] - raw["total_solar_gain"], 0.0), 2)
            overall_score = round(
                max(raw["comfort_percentage"] - energy_requirement / 100.0, 0.0), 2
            )

            metrics.append(
                ComparisonMetric(
                    design_id=design_id,
                    comfort_percentage=raw["comfort_percentage"],
                    total_heat_loss=raw["total_heat_loss"],
                    total_solar_gain=raw["total_solar_gain"],
                    energy_requirement=energy_requirement,
                    overall_score=overall_score,
                )
            )

        best = max(metrics, key=lambda m: m.overall_score)
        logger.info("Compared %d designs; best=%s", len(design_ids), best.design_id)

        return ComparisonResponse(
            design_ids=design_ids,
            metrics=metrics,
            best_design_id=best.design_id,
        )
