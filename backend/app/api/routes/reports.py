from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse

from app.dependencies import get_report_service
from app.services.report_service import ReportService

router = APIRouter(prefix="/projects", tags=["reports"])


@router.get("/{project_id}/report", summary="Generate a structured JSON report for a project")
def get_report(
    project_id: str,
    climate_location: str = Query("Composite", description="Climate preset to use for the report"),
    service: ReportService = Depends(get_report_service),
):
    return service.build_report(project_id, climate_location)


@router.get(
    "/{project_id}/report/markdown",
    response_class=PlainTextResponse,
    summary="Generate a Markdown report for a project",
)
def get_report_markdown(
    project_id: str,
    climate_location: str = Query("Composite", description="Climate preset to use for the report"),
    service: ReportService = Depends(get_report_service),
):
    return service.build_markdown_report(project_id, climate_location)
