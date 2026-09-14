"""
Tests 10-11: Optimization run creation + candidate creation.
"""
from app.models.optimization import OptimizationStatus
from app.repositories.design_repository import DesignRepository
from app.repositories.optimization_repository import OptimizationRepository
from app.repositories.project_repository import ProjectRepository


def _make_project_and_design(db_session):
    project = ProjectRepository(db_session).create(name="Opt Test Project")
    design = DesignRepository(db_session).create(
        project_id=project.id, length=6, width=5, height=3,
        wall_thickness=0.3, roof_thickness=0.2, floor_thickness=0.15,
        is_baseline=True,
    )
    return project, design


def test_optimization_run_creation(db_session):
    project, design = _make_project_and_design(db_session)
    repo = OptimizationRepository(db_session)
    run = repo.create(
        project_id=project.id,
        baseline_design_id=design.id,
        algorithm="NSGA-II",
        status=OptimizationStatus.CREATED,
        candidate_count=20,
        iterations=50,
    )
    assert run.id is not None
    assert run.status == OptimizationStatus.CREATED


def test_optimization_candidate_creation(db_session):
    project, design = _make_project_and_design(db_session)
    design_repo = DesignRepository(db_session)
    candidate_design = design_repo.create(
        project_id=project.id, length=6.5, width=5, height=3,
        wall_thickness=0.35, roof_thickness=0.2, floor_thickness=0.15,
    )

    repo = OptimizationRepository(db_session)
    run = repo.create(project_id=project.id, baseline_design_id=design.id)

    candidate = repo.add_candidate(
        run.id,
        design_id=candidate_design.id,
        generation=1,
        score=0.87,
        comfort_score=0.9,
        heat_loss_score=0.8,
        energy_score=0.85,
        cost_score=0.75,
        rank=1,
    )
    assert candidate.id is not None

    candidates = repo.list_candidates(run.id)
    assert len(candidates) == 1
    assert candidates[0].rank == 1
