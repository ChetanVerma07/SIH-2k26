import pytest

from ansys_thermal.models.climate import (
    BoundaryConditions,
    HourlyClimatePoint,
    build_constant_climate,
    build_diurnal_climate,
)
from ansys_thermal.validation.validators import validate_boundary_conditions, ValidationError


def test_build_constant_climate_length():
    series = build_constant_climate(ambient_temp_c=20.0, duration_hours=10.0, time_step_s=3600.0)
    assert len(series) == 11  # 0..10 inclusive at 1-hour steps
    assert all(p.ambient_temp_c == 20.0 for p in series)


def test_build_diurnal_climate_bounds():
    series = build_diurnal_climate(
        mean_temp_c=10.0, amplitude_c=5.0, duration_hours=24.0, time_step_s=3600.0
    )
    temps = [p.ambient_temp_c for p in series]
    assert max(temps) <= 15.01
    assert min(temps) >= 4.99
    # Solar should be zero at night and positive at midday
    night_point = next(p for p in series if p.hour == 0.0)
    midday_point = min(series, key=lambda p: abs(p.hour - 14.0))
    assert night_point.solar_irradiance_w_m2 == 0.0
    assert midday_point.solar_irradiance_w_m2 > 0.0


def test_valid_boundary_conditions_pass(simple_boundary_conditions):
    validate_boundary_conditions(simple_boundary_conditions)  # should not raise


def test_too_few_points_rejected():
    bc = BoundaryConditions(ambient_series=[HourlyClimatePoint(hour=0, ambient_temp_c=20.0)])
    with pytest.raises(ValidationError):
        validate_boundary_conditions(bc)


def test_implausible_ambient_temp_rejected(simple_boundary_conditions):
    simple_boundary_conditions.ambient_series[0].ambient_temp_c = 500.0
    with pytest.raises(ValidationError):
        validate_boundary_conditions(simple_boundary_conditions)


def test_negative_solar_irradiance_rejected(simple_boundary_conditions):
    simple_boundary_conditions.ambient_series[0].solar_irradiance_w_m2 = -10.0
    with pytest.raises(ValidationError):
        validate_boundary_conditions(simple_boundary_conditions)


def test_zero_time_step_rejected(simple_boundary_conditions):
    simple_boundary_conditions.time_step_s = 0.0
    with pytest.raises(ValidationError):
        validate_boundary_conditions(simple_boundary_conditions)


def test_excessive_step_count_rejected(simple_boundary_conditions):
    simple_boundary_conditions.time_step_s = 1.0
    simple_boundary_conditions.duration_hours = 1_000_000.0
    with pytest.raises(ValidationError):
        validate_boundary_conditions(simple_boundary_conditions)


def test_boundary_conditions_round_trip(simple_boundary_conditions):
    d = simple_boundary_conditions.as_dict()
    restored = BoundaryConditions.from_dict(d)
    assert len(restored.ambient_series) == len(simple_boundary_conditions.ambient_series)
    assert restored.indoor_initial_temp_c == simple_boundary_conditions.indoor_initial_temp_c
