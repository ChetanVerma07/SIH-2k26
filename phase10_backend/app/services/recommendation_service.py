from fastapi import HTTPException, status

from app.core.logging import logger
from app.schemas.recommendation import RecommendationResponse
from app.services.climate_service import ClimateService
from app.services.design_service import DesignService
from app.services.project_service import ProjectService
from app.services.material_service import MaterialService
from app.services.thermal_engine import MockThermalEngine, ThermalEngine

ASSUMPTIONS = [
    "Thermal performance is estimated using a simplified deterministic mock engine, not full CFD/ANSYS analysis.",
    "Material properties are taken from standard reference values and may not reflect exact local materials.",
    "Climate data used is either a regional preset or user-supplied and assumed constant/representative unless a time-series is provided.",
    "Occupant internal heat gains and mechanical HVAC systems are not modeled in this phase.",
]

LIMITATIONS = [
    "Results are indicative only and must be validated with detailed simulation (e.g. ANSYS) before construction.",
    "The optimizer searches a small, discrete set of insulation/opening combinations, not a full design space.",
    "Structural, cost, and material availability constraints are not evaluated in this phase.",
]


class RecommendationService:
    def __init__(
        self,
        project_service: ProjectService,
        design_service: DesignService,
        climate_service: ClimateService,
        material_service: MaterialService,
        thermal_engine: ThermalEngine = None,
    ):
        self.project_service = project_service
        self.design_service = design_service
        self.climate_service = climate_service
        self.material_service = material_service
        self.thermal_engine = thermal_engine or MockThermalEngine()

    def recommend(self, project_id: str, climate_location: str = "Composite") -> RecommendationResponse:
        project = self.project_service.get_project(project_id)

        if not project.design_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{project_id}' has no designs to recommend from",
            )

        climate = self.climate_service.get_by_location(climate_location)

        best_design_id = None
        best_score = -1.0
        best_performance = {}
        baseline_performance = None

        for idx, design_id in enumerate(project.design_ids):
            design = self.design_service.get_design(design_id)
            materials = {
                "wall_material": self.material_service.get_material(design.wall_material),
                "roof_material": self.material_service.get_material(design.roof_material),
                "floor_material": self.material_service.get_material(design.floor_material),
                "insulation_material": self.material_service.get_material(design.insulation_material),
            }
            raw = self.thermal_engine.simulate(design, climate, materials, duration=24, timestep=1)
            penalty = raw["total_heat_loss"] / (raw["total_heat_loss"] + 1000.0) * 100.0
            score = round(max(raw["comfort_percentage"] - 0.5 * penalty, 0.0), 2)

            if idx == 0:
                baseline_performance = raw

            if score > best_score:
                best_score = score
                best_design_id = design_id
                best_performance = raw

        explanation = (
            f"Design {best_design_id} was selected because it provides the highest comfort "
            f"percentage ({best_performance['comfort_percentage']}%) while keeping predicted "
            f"heat loss ({best_performance['total_heat_loss']}) relatively low, compared with "
            f"the other {len(project.design_ids)} design(s) evaluated for this project."
        )

        logger.info("Recommendation for project %s: %s (score=%s)", project_id, best_design_id, best_score)

        return RecommendationResponse(
            project_id=project_id,
            recommended_design_id=best_design_id,
            score=best_score,
            performance=best_performance,
            explanation=explanation,
            assumptions=ASSUMPTIONS,
            limitations=LIMITATIONS,
        )
