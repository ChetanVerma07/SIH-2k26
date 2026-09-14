"""
Tests 14-16: FK relationships, constraints, rollback/error handling.
"""
import pytest
from sqlalchemy.exc import IntegrityError

from app.repositories.design_repository import DesignRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.simulation_repository import SimulationRepository


def test_foreign_key_relationship_project_designs(db_session):
    project = ProjectRepository(db_session).create(name="FK Test Project")
    design_repo = DesignRepository(db_session)
    design_repo.create(
        project_id=project.id, length=6, width=5, height=3,
        wall_thickness=0.3, roof_thickness=0.2, floor_thickness=0.15,
    )
    db_session.refresh(project)
    assert len(project.designs) == 1
    assert project.designs[0].project is project


def test_check_constraint_opening_percentage(db_session):
    project = ProjectRepository(db_session).create(name="Constraint Test Project")
    repo = DesignRepository(db_session)
    with pytest.raises(IntegrityError):
        repo.create(
            project_id=project.id, length=6, width=5, height=3,
            wall_thickness=0.3, roof_thickness=0.2, floor_thickness=0.15,
            opening_percentage=150,  # invalid: > 100
        )


def test_foreign_key_violation_raises(db_session):
    import uuid
    repo = SimulationRepository(db_session)
    with pytest.raises(IntegrityError):
        repo.create(
            project_id=uuid.uuid4(),  # non-existent project
            design_id=uuid.uuid4(),   # non-existent design
        )


def test_rollback_on_error_leaves_no_partial_row(db_session):
    repo = ProjectRepository(db_session)
    count_before = len(repo.list())

    savepoint = db_session.begin_nested()
    try:
        repo.create(name="Will be rolled back")
        raise RuntimeError("simulated failure")
    except RuntimeError:
        savepoint.rollback()

    count_after = len(repo.list())
    assert count_after == count_before
