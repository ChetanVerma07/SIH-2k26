import pytest

from ansys_thermal.models.geometry import ShelterGeometry, ShelterShape
from ansys_thermal.validation.validators import validate_geometry, ValidationError


def test_geometry_derived_quantities(simple_geometry):
    assert simple_geometry.floor_area() == pytest.approx(15.0)
    assert simple_geometry.roof_area() == pytest.approx(15.0)
    expected_gross = 2 * (5.0 + 3.0) * 2.5
    assert simple_geometry.wall_gross_area() == pytest.approx(expected_gross)
    assert simple_geometry.total_opening_area() == pytest.approx(3.3)
    assert simple_geometry.wall_net_area() == pytest.approx(expected_gross - 3.3)
    assert simple_geometry.internal_volume() == pytest.approx(5.0 * 3.0 * 2.5)


def test_geometry_round_trip_dict(simple_geometry):
    d = simple_geometry.as_dict()
    restored = ShelterGeometry.from_dict(d)
    assert restored.length == simple_geometry.length
    assert restored.width == simple_geometry.width
    assert restored.shape == ShelterShape.RECTANGULAR


def test_valid_geometry_passes(simple_geometry):
    validate_geometry(simple_geometry)  # should not raise


def test_negative_length_rejected(simple_geometry):
    simple_geometry.length = -1.0
    with pytest.raises(ValidationError):
        validate_geometry(simple_geometry)


def test_zero_wall_thickness_rejected(simple_geometry):
    simple_geometry.wall_thickness = 0.0
    with pytest.raises(ValidationError):
        validate_geometry(simple_geometry)


def test_wall_thickness_too_large_rejected(simple_geometry):
    simple_geometry.wall_thickness = 10.0  # bigger than half of width/length
    with pytest.raises(ValidationError):
        validate_geometry(simple_geometry)


def test_openings_exceeding_wall_area_rejected(simple_geometry):
    simple_geometry.window_area = 10000.0
    with pytest.raises(ValidationError):
        validate_geometry(simple_geometry)


def test_negative_opening_area_rejected(simple_geometry):
    simple_geometry.door_area = -1.0
    with pytest.raises(ValidationError):
        validate_geometry(simple_geometry)


def test_orientation_out_of_range_rejected(simple_geometry):
    simple_geometry.orientation_deg = 400.0
    with pytest.raises(ValidationError):
        validate_geometry(simple_geometry)


def test_sanity_bound_length_rejected(simple_geometry):
    simple_geometry.length = 1000.0
    with pytest.raises(ValidationError):
        validate_geometry(simple_geometry)
