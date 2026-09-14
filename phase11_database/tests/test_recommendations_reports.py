"""
Tests 12-13: Recommendation creation + Report creation.
"""
from app.models.report import ReportFormat
from app.repositories.design_repository import DesignRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.report_repository import ReportRepository


def test_recommendation_creation(db_session):
    project = ProjectRepository(db_session).create(name="Rec Test Project")
    design = DesignRepository(db_session).create(
        project_id=project.id, length=6, width=5, height=3,
        wall_thickness=0.3, roof_thickness=0.2, floor_thickness=0.15,
    )
    repo = RecommendationRepository(db_session)
    rec = repo.create(
        project_id=project.id,
        design_id=design.id,
        score=0.91,
        explanation="Selected for best comfort/cost trade-off.",
        trade_offs={"cost_vs_comfort": "moderate"},
        assumptions={"occupancy": "4 people"},
        limitations={"simulation_backend": "MOCK"},
    )
    assert rec.id is not None
    assert rec.trade_offs["cost_vs_comfort"] == "moderate"

    recs = repo.list_by_project(project.id)
    assert len(recs) == 1


def test_report_creation(db_session):
    project = ProjectRepository(db_session).create(name="Report Test Project")
    repo = ReportRepository(db_session)
    report = repo.create(
        project_id=project.id,
        title="Passive Design Summary",
        format=ReportFormat.MARKDOWN,
        content="# Summary\nBaseline design meets comfort targets.",
    )
    assert report.id is not None
    assert report.format == ReportFormat.MARKDOWN
