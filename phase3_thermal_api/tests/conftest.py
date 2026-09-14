import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.material import Material
from app.models.shelter import OpeningProperties, ShelterConfig


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def wall_material() -> Material:
    return Material(
        name="Rammed Earth",
        thermal_conductivity=0.7,
        density=2000,
        specific_heat=800,
        thickness=0.4,
        solar_absorptivity=0.65,
        emissivity=0.9,
    )


@pytest.fixture
def roof_material() -> Material:
    return Material(
        name="Timber Deck",
        thermal_conductivity=0.14,
        density=500,
        specific_heat=1600,
        thickness=0.05,
        solar_absorptivity=0.6,
        emissivity=0.9,
    )


@pytest.fixture
def floor_material() -> Material:
    return Material(
        name="Concrete Slab",
        thermal_conductivity=1.4,
        density=2300,
        specific_heat=880,
        thickness=0.15,
        solar_absorptivity=0.6,
        emissivity=0.9,
    )


@pytest.fixture
def basic_shelter(wall_material, roof_material, floor_material) -> ShelterConfig:
    return ShelterConfig(
        name="Test Shelter",
        length=6.0,
        width=4.0,
        height=2.7,
        orientation="S",
        wall_material=wall_material,
        roof_material=roof_material,
        floor_material=floor_material,
        openings=OpeningProperties(
            window_area=2.0, door_area=1.5, other_opening_area=0.0
        ),
        structural_mass_fraction=0.3,
    )


@pytest.fixture
def basic_settings() -> dict:
    return {
        "duration_hours": 24,
        "time_step_minutes": 30,
        "initial_indoor_temperature": 10.0,
        "comfort_min": 15.0,
        "comfort_max": 24.0,
    }


@pytest.fixture
def constant_climate() -> dict:
    return {"ambient_temperature": -10.0, "solar_radiation": 300.0}


@pytest.fixture
def timeseries_climate() -> list:
    return [
        {"time": 0, "ambient_temperature": -10.0, "solar_radiation": 0.0},
        {"time": 6, "ambient_temperature": -14.0, "solar_radiation": 0.0},
        {"time": 12, "ambient_temperature": -2.0, "solar_radiation": 600.0},
        {"time": 18, "ambient_temperature": -8.0, "solar_radiation": 50.0},
        {"time": 24, "ambient_temperature": -11.0, "solar_radiation": 0.0},
    ]
