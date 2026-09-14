"""
Test 2: Project CRUD.
"""
from app.repositories.project_repository import ProjectRepository


def test_project_create_and_get(db_session):
    repo = ProjectRepository(db_session)
    project = repo.create(
        name="Ladakh Field Station",
        location="Leh, Ladakh",
        latitude=34.15,
        longitude=77.58,
        climate_type="COLD_HIGH_ALTITUDE",
    )
    assert project.id is not None

    fetched = repo.get(project.id)
    assert fetched is not None
    assert fetched.name == "Ladakh Field Station"


def test_project_update(db_session):
    repo = ProjectRepository(db_session)
    project = repo.create(name="Original Name", location="Delhi")
    updated = repo.update(project.id, name="Renamed Project")
    assert updated.name == "Renamed Project"


def test_project_delete(db_session):
    repo = ProjectRepository(db_session)
    project = repo.create(name="Temp Project")
    repo.delete(project.id)
    assert repo.get(project.id) is None


def test_project_list_by_location(db_session):
    repo = ProjectRepository(db_session)
    repo.create(name="P1", location="Chennai")
    repo.create(name="P2", location="Chennai")
    repo.create(name="P3", location="Delhi")
    results = repo.list_by_location("Chennai")
    assert len(results) == 2
