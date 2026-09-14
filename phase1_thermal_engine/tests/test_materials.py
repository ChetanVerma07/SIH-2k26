"""Tests for thermal_engine.materials."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from thermal_engine.materials import EXAMPLE_MATERIALS, Material
from thermal_engine.validation import ThermalEngineValidationError


def test_material_creation_valid():
    m = Material(
        name="Test Brick",
        thermal_conductivity=0.7,
        density=1700.0,
        specific_heat=840.0,
        thickness=0.23,
        solar_absorptivity=0.6,
        emissivity=0.9,
    )
    assert m.name == "Test Brick"
    assert m.thermal_conductivity == pytest.approx(0.7)
    assert m.u_value == pytest.approx(0.7 / 0.23)
    assert m.thermal_resistance == pytest.approx(0.23 / 0.7)


def test_material_u_value_and_heat_capacity_formulas():
    m = Material(
        name="Slab",
        thermal_conductivity=1.0,
        density=2000.0,
        specific_heat=900.0,
        thickness=0.2,
        solar_absorptivity=0.5,
    )
    assert m.u_value == pytest.approx(5.0)  # 1.0 / 0.2
    assert m.mass_per_unit_area() == pytest.approx(400.0)  # 2000 * 0.2
    assert m.heat_capacity_per_unit_area() == pytest.approx(360000.0)  # 400 * 900


@pytest.mark.parametrize(
    "field,value",
    [
        ("thermal_conductivity", 0.0),
        ("thermal_conductivity", -1.0),
        ("density", -5.0),
        ("specific_heat", 0.0),
        ("thickness", 0.0),
        ("thickness", -0.1),
        ("solar_absorptivity", -0.1),
        ("solar_absorptivity", 1.5),
        ("emissivity", 1.2),
    ],
)
def test_material_invalid_values_raise(field, value):
    valid_kwargs = dict(
        name="Bad Material",
        thermal_conductivity=0.5,
        density=1000.0,
        specific_heat=900.0,
        thickness=0.1,
        solar_absorptivity=0.5,
        emissivity=0.9,
    )
    valid_kwargs[field] = value
    with pytest.raises(ThermalEngineValidationError):
        Material(**valid_kwargs)


def test_material_invalid_name_raises():
    with pytest.raises(ThermalEngineValidationError):
        Material(
            name="   ",
            thermal_conductivity=0.5,
            density=1000.0,
            specific_heat=900.0,
            thickness=0.1,
            solar_absorptivity=0.5,
        )


def test_example_materials_are_all_valid_and_nonempty():
    assert len(EXAMPLE_MATERIALS) > 0
    for key, material in EXAMPLE_MATERIALS.items():
        assert isinstance(material, Material)
        assert material.u_value > 0
        assert isinstance(key, str) and key
