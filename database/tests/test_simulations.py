"""
Tests 8-9: Simulation creation + simulation result insertion.
"""
from datetime import datetime, timedelta, timezone

from app.models.simulation import SimulationBackend, SimulationStatus
from app.repositories.design_repository import DesignRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.simulation_repository import SimulationRepository


def _make_design(db_session):
    project = ProjectRepository(db_session).create(name="Sim Test Project")
    design = DesignRepository(db_session).create(
        project_id=project.id, length=6, width=5, height=3,
        wall_thickness=0.3, roof_thickness=0.2, floor_thickness=0.15,
    )
    return project, design


def test_simulation_creation(db_session):
    project, design = _make_design(db_session)
    repo = SimulationRepository(db_session)
    sim = repo.create(
        project_id=project.id,
        design_id=design.id,
        duration_hours=24,
        timestep_minutes=60,
        status=SimulationStatus.CREATED,
        backend=SimulationBackend.MOCK,
    )
    assert sim.id is not None
    assert sim.status == SimulationStatus.CREATED


def test_simulation_result_insertion(db_session):
    project, design = _make_design(db_session)
    repo = SimulationRepository(db_session)
    sim = repo.create(project_id=project.id, design_id=design.id)

    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    rows = [
        dict(
            timestamp=base + timedelta(hours=h),
            indoor_temperature=18 + h * 0.1,
            outdoor_temperature=-5 + h * 0.2,
            heat_loss=120.5,
            solar_gain=40.2,
            comfort_status="COMFORTABLE",
        )
        for h in range(24)
    ]
    inserted = repo.bulk_add_results(sim.id, rows)
    assert len(inserted) == 24

    results = repo.get_results(sim.id)
    assert len(results) == 24
    assert results[0].timestamp <= results[-1].timestamp
