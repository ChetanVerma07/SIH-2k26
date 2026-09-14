"""Shared pytest fixtures for the ansys_thermal test suite."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from ansys_thermal.models.geometry import ShelterGeometry
from ansys_thermal.models.materials import MaterialAssignment, get_example_material
from ansys_thermal.models.climate import BoundaryConditions, build_constant_climate
from ansys_thermal.models.simulation import SimulationConfig


@pytest.fixture
def simple_geometry() -> ShelterGeometry:
    return ShelterGeometry(
        length=5.0,
        width=3.0,
        height=2.5,
        wall_thickness=0.3,
        roof_thickness=0.2,
        floor_thickness=0.15,
        window_area=1.5,
        door_area=1.8,
        other_openings_area=0.0,
        orientation_deg=180.0,
    )


@pytest.fixture
def simple_materials() -> MaterialAssignment:
    return MaterialAssignment(
        wall_material=get_example_material("burnt_clay_brick"),
        roof_material=get_example_material("concrete_dense"),
        floor_material=get_example_material("concrete_dense"),
        window_material=get_example_material("single_glass"),
    )


@pytest.fixture
def simple_boundary_conditions() -> BoundaryConditions:
    series = build_constant_climate(
        ambient_temp_c=25.0,
        duration_hours=12.0,
        time_step_s=3600.0,
        solar_irradiance_w_m2=400.0,
    )
    return BoundaryConditions(
        ambient_series=series,
        indoor_initial_temp_c=22.0,
        time_step_s=3600.0,
        duration_hours=12.0,
    )


@pytest.fixture
def simple_config(simple_geometry, simple_materials, simple_boundary_conditions) -> SimulationConfig:
    return SimulationConfig(
        name="test_shelter",
        geometry=simple_geometry,
        materials=simple_materials,
        boundary_conditions=simple_boundary_conditions,
    )
