import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories.memory_repository import repository_registry


@pytest.fixture(autouse=True)
def _reset_repositories():
    """
    Ensure each test starts with fresh project/design/simulation/optimization data.

    Materials and climate presets are intentionally NOT cleared here: they are
    seeded once into MaterialService/ClimateService (both process-lifetime
    singletons via lru_cache) on first construction, and those services track
    their own "already loaded" state separately from the repository contents.
    Clearing the repositories for those two would leave the seed data gone
    with no re-seed trigger.
    """
    repository_registry.projects.clear()
    repository_registry.designs.clear()
    repository_registry.simulations.clear()
    repository_registry.optimizations.clear()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_materials(client):
    resp = client.get("/api/v1/materials")
    materials = resp.json()
    by_category = {}
    for m in materials:
        by_category.setdefault(m["category"], []).append(m)
    return {
        "wall_material": by_category["wall"][0]["id"],
        "roof_material": by_category["roof"][0]["id"],
        "floor_material": by_category["floor"][0]["id"],
        "insulation_material": by_category["insulation"][0]["id"],
    }


@pytest.fixture
def sample_project(client):
    resp = client.post(
        "/api/v1/projects",
        json={"name": "Ladakh Winter Shelter", "location": "Leh, Ladakh, India", "description": "Test project"},
    )
    assert resp.status_code == 201
    return resp.json()


def make_design_payload(materials, project_id=None, insulation_thickness=0.08, opening_percentage=10):
    payload = {
        "length": 8.0,
        "width": 6.0,
        "height": 3.0,
        "wall_thickness": 0.4,
        "roof_thickness": 0.2,
        "floor_thickness": 0.15,
        "insulation_thickness": insulation_thickness,
        "opening_percentage": opening_percentage,
        "orientation": "S",
        "occupants": 4,
        "floor_area": 48.0,
        "target_min_temperature": 18.0,
        "target_max_temperature": 26.0,
        **materials,
    }
    if project_id:
        payload["project_id"] = project_id
    return payload


@pytest.fixture
def sample_design(client, sample_project, sample_materials):
    payload = make_design_payload(sample_materials, project_id=sample_project["id"])
    resp = client.post("/api/v1/designs", json=payload)
    assert resp.status_code == 201
    return resp.json()
