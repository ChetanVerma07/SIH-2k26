import pytest

from ansys_thermal.models.materials import (
    Material,
    MaterialAssignment,
    EXAMPLE_MATERIALS,
    get_example_material,
)
from ansys_thermal.validation.validators import (
    validate_material,
    validate_material_assignment,
    ValidationError,
)


def test_get_example_material_valid_key():
    mat = get_example_material("rammed_earth")
    assert mat.name == "Rammed Earth"
    assert mat.thermal_conductivity_w_mk > 0


def test_get_example_material_invalid_key_raises():
    with pytest.raises(KeyError):
        get_example_material("unobtainium")


def test_all_example_materials_are_valid():
    for key, mat in EXAMPLE_MATERIALS.items():
        validate_material(mat, key)  # should not raise


def test_material_thermal_diffusivity():
    mat = Material(
        name="test",
        thermal_conductivity_w_mk=1.0,
        density_kg_m3=1000.0,
        specific_heat_j_kgk=1000.0,
    )
    assert mat.thermal_diffusivity_m2_s() == pytest.approx(1.0e-6)


def test_material_round_trip_dict():
    mat = get_example_material("aac_block")
    d = mat.as_dict()
    restored = Material.from_dict(d)
    assert restored.name == mat.name
    assert restored.thermal_conductivity_w_mk == mat.thermal_conductivity_w_mk


def test_negative_conductivity_rejected():
    mat = Material(
        name="bad",
        thermal_conductivity_w_mk=-1.0,
        density_kg_m3=1000.0,
        specific_heat_j_kgk=1000.0,
    )
    with pytest.raises(ValidationError):
        validate_material(mat)


def test_emissivity_out_of_range_rejected():
    mat = Material(
        name="bad",
        thermal_conductivity_w_mk=1.0,
        density_kg_m3=1000.0,
        specific_heat_j_kgk=1000.0,
        emissivity=1.5,
    )
    with pytest.raises(ValidationError):
        validate_material(mat)


def test_material_assignment_round_trip(simple_materials):
    d = simple_materials.as_dict()
    restored = MaterialAssignment.from_dict(d)
    assert restored.wall_material.name == simple_materials.wall_material.name


def test_valid_material_assignment_passes(simple_materials):
    validate_material_assignment(simple_materials)  # should not raise
