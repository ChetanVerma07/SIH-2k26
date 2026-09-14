import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from optimizer.models.design import ShelterDesign, DEFAULT_CONSTRAINTS
from optimizer.models.materials import get_material, structural_materials, insulation_materials


def make_valid_design():
    return ShelterDesign(
        length=6.0, width=5.0, height=2.8,
        wall_thickness=0.25, roof_thickness=0.20, floor_thickness=0.15,
        insulation_thickness=0.10,
        wall_material="rammed_earth", roof_material="timber_frame",
        floor_material="stone_masonry", insulation_material="mineral_wool",
        opening_area=3.0, door_area=2.0, orientation=0.0,
    )


def test_valid_design_passes_validation():
    design = make_valid_design()
    assert design.is_valid()
    assert design.validate() == []


def test_invalid_length_is_rejected():
    design = make_valid_design()
    design.length = 1.0  # below min
    errors = design.validate()
    assert any("length" in e for e in errors)


def test_aspect_ratio_constraint():
    design = make_valid_design()
    design.length = 10.0
    design.width = 3.0  # ratio > 2.5
    errors = design.validate()
    assert any("aspect_ratio" in e for e in errors)


def test_opening_area_bounds():
    design = make_valid_design()
    design.opening_area = 100.0  # way too much
    errors = design.validate()
    assert any("opening_area" in e for e in errors)


def test_floor_area_and_volume():
    design = make_valid_design()
    assert design.floor_area() == design.length * design.width
    assert design.volume() == design.length * design.width * design.height


def test_material_lookup():
    mat = get_material("mineral_wool")
    assert mat.category == "insulation"
    assert mat.conductivity > 0


def test_material_categories_nonempty():
    assert len(structural_materials()) >= 3
    assert len(insulation_materials()) >= 3


def test_unknown_material_raises():
    import pytest
    with pytest.raises(KeyError):
        get_material("unobtainium")
