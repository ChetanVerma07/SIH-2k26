import pytest

from ansys_thermal.geometry.shelter_builder import build_rectangular_shelter
from ansys_thermal.models.geometry import ShelterGeometry, ShelterShape


def test_build_rectangular_shelter_element_types(simple_geometry):
    plan = build_rectangular_shelter(simple_geometry)
    types = {e.element_type for e in plan.elements}
    assert "wall" in types
    assert "roof" in types
    assert "floor" in types
    assert "opening" in types  # simple_geometry has window+door area > 0


def test_build_rectangular_shelter_area_conservation(simple_geometry):
    plan = build_rectangular_shelter(simple_geometry)
    wall_area = plan.total_area_by_type("wall")
    opening_area = plan.total_area_by_type("opening")
    # Net wall area + opening area should equal gross wall area (conservation)
    assert wall_area + opening_area == pytest.approx(simple_geometry.wall_gross_area(), abs=1e-6)


def test_build_rectangular_shelter_roof_and_floor_area(simple_geometry):
    plan = build_rectangular_shelter(simple_geometry)
    assert plan.total_area_by_type("roof") == pytest.approx(simple_geometry.roof_area())
    assert plan.total_area_by_type("floor") == pytest.approx(simple_geometry.floor_area())


def test_build_rectangular_shelter_rejects_other_shapes():
    geom = ShelterGeometry(
        length=5, width=3, height=2.5, wall_thickness=0.3,
        roof_thickness=0.2, floor_thickness=0.15,
    )
    geom.shape = "dome"  # not a real supported shape
    with pytest.raises(NotImplementedError):
        build_rectangular_shelter(geom)


def test_no_openings_case():
    geom = ShelterGeometry(
        length=4, width=4, height=2.5, wall_thickness=0.2,
        roof_thickness=0.15, floor_thickness=0.1,
        window_area=0.0, door_area=0.0, other_openings_area=0.0,
    )
    plan = build_rectangular_shelter(geom)
    types = {e.element_type for e in plan.elements}
    assert "opening" not in types
