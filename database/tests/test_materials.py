"""
Test 3: Material CRUD.
"""
import pytest
from sqlalchemy.exc import IntegrityError

from app.models.material import MaterialCategory
from app.repositories.material_repository import MaterialRepository


def test_material_create_and_get(db_session):
    repo = MaterialRepository(db_session)
    material = repo.create(
        name="Test Brick",
        category=MaterialCategory.WALL,
        thermal_conductivity=0.72,
        density=1700,
        specific_heat=840,
        emissivity=0.9,
        solar_absorptivity=0.7,
        cost_factor=0.85,
    )
    assert material.id is not None
    assert repo.get_by_name("Test Brick").id == material.id


def test_material_list_by_category(db_session):
    repo = MaterialRepository(db_session)
    repo.create(
        name="Wool A", category=MaterialCategory.INSULATION,
        thermal_conductivity=0.04, density=100, specific_heat=840,
        emissivity=0.9, solar_absorptivity=0.5, cost_factor=1.0,
    )
    results = repo.list_by_category(MaterialCategory.INSULATION)
    assert len(results) == 1


def test_material_positive_thermal_conductivity_constraint(db_session):
    repo = MaterialRepository(db_session)
    with pytest.raises(IntegrityError):
        repo.create(
            name="Bad Material", category=MaterialCategory.WALL,
            thermal_conductivity=-1, density=100, specific_heat=800,
            emissivity=0.9, solar_absorptivity=0.5, cost_factor=1.0,
        )
