from dataclasses import asdict
from typing import Any, Dict

from app.core.logging import logger
from app.services.climate_service import ClimateService
from app.services.comparison_service import ComparisonService
from app.services.design_service import DesignService
from app.services.material_service import MaterialService
from app.services.project_service import ProjectService
from app.services.recommendation_service import ASSUMPTIONS, LIMITATIONS, RecommendationService


class ReportService:
    def __init__(
        self,
        project_service: ProjectService,
        design_service: DesignService,
        climate_service: ClimateService,
        material_service: MaterialService,
        recommendation_service: RecommendationService,
        comparison_service: ComparisonService,
    ):
        self.project_service = project_service
        self.design_service = design_service
        self.climate_service = climate_service
        self.material_service = material_service
        self.recommendation_service = recommendation_service
        self.comparison_service = comparison_service

    def build_report(self, project_id: str, climate_location: str = "Composite") -> Dict[str, Any]:
        project = self.project_service.get_project(project_id)
        climate = self.climate_service.get_by_location(climate_location)

        designs = [self.design_service.get_design(d_id) for d_id in project.design_ids]

        recommendation = None
        comparison = None
        if project.design_ids:
            recommendation = self.recommendation_service.recommend(project_id, climate_location)
        if len(project.design_ids) >= 2:
            comparison = self.comparison_service.compare(project.design_ids, climate_location)

        materials_used = {}
        for design in designs:
            for field_name in ("wall_material", "roof_material", "floor_material", "insulation_material"):
                material_id = getattr(design, field_name)
                if material_id not in materials_used:
                    materials_used[material_id] = asdict(self.material_service.get_material(material_id))

        report = {
            "project": {
                "id": project.id,
                "name": project.name,
                "location": project.location,
                "description": project.description,
                "created_at": project.created_at.isoformat(),
            },
            "climate": asdict(climate),
            "designs": [asdict(d) for d in designs],
            "materials": materials_used,
            "recommendation": recommendation.model_dump() if recommendation else None,
            "comparison": comparison.model_dump() if comparison else None,
            "assumptions": ASSUMPTIONS,
            "limitations": LIMITATIONS,
        }
        logger.info("Generated JSON report for project %s", project_id)
        return report

    def build_markdown_report(self, project_id: str, climate_location: str = "Composite") -> str:
        report = self.build_report(project_id, climate_location)

        lines = [
            f"# Project Report: {report['project']['name']}",
            "",
            f"**Location:** {report['project']['location']}  ",
            f"**Project ID:** {report['project']['id']}  ",
            f"**Created:** {report['project']['created_at']}",
            "",
            "## Climate",
            f"- Location: {report['climate'].get('location')}",
            f"- Temperature: {report['climate']['temperature']} °C",
            f"- Humidity: {report['climate']['humidity']} %",
            f"- Solar Radiation: {report['climate']['solar_radiation']} W/m²",
            f"- Wind Speed: {report['climate']['wind_speed']} km/h",
            "",
            "## Designs",
        ]

        for d in report["designs"]:
            lines.append(
                f"- **{d['id']}**: {d['length']}m x {d['width']}m x {d['height']}m, "
                f"insulation {d['insulation_thickness']}m, openings {d['opening_percentage']}%"
            )

        lines.append("")
        lines.append("## Materials")
        for mat_id, mat in report["materials"].items():
            lines.append(f"- **{mat['name']}** ({mat['category']}): k={mat['thermal_conductivity']} W/m.K")

        lines.append("")
        lines.append("## Recommendation")
        rec = report["recommendation"]
        if rec:
            lines.append(f"- Recommended design: **{rec['recommended_design_id']}**")
            lines.append(f"- Score: {rec['score']}")
            lines.append(f"- Explanation: {rec['explanation']}")
        else:
            lines.append("- No designs available for recommendation.")

        lines.append("")
        lines.append("## Comparison")
        comp = report["comparison"]
        if comp:
            for m in comp["metrics"]:
                lines.append(
                    f"- {m['design_id']}: comfort={m['comfort_percentage']}%, "
                    f"heat_loss={m['total_heat_loss']}, score={m['overall_score']}"
                )
            lines.append(f"- Best design: **{comp['best_design_id']}**")
        else:
            lines.append("- Not enough designs to compare.")

        lines.append("")
        lines.append("## Assumptions")
        for a in report["assumptions"]:
            lines.append(f"- {a}")

        lines.append("")
        lines.append("## Limitations")
        for l in report["limitations"]:
            lines.append(f"- {l}")

        return "\n".join(lines)
