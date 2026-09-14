"""Tests for thermal_engine.shelter, thermal_engine.simulation and
thermal_engine.comparison."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from thermal_engine.comparison import compare_designs
from thermal_engine.materials import EXAMPLE_MATERIALS, Material
from thermal_engine.shelter import Shelter
from thermal_engine.simulation import simulate_shelter
from thermal_engine.validation import ThermalEngineValidationError


def make_shelter(**overrides) -> Shelter:
    defaults = dict(
        name="Test Shelter",
        length=5.0,
        width=4.0,
        height=2.5,
        wall_material=EXAMPLE_MATERIALS["fired_brick"],
        roof_material=EXAMPLE_MATERIALS["cgi_sheet_roof"],
        floor_material=EXAMPLE_MATERIALS["concrete"],
        num_openings=1,
        opening_area_each=1.5,
        opening_u_value=2.8,
        initial_indoor_temperature=10.0,
    )
    defaults.update(overrides)
    return Shelter(**defaults)


# --- Shelter geometry ------------------------------------------------------


def test_shelter_geometry_calculations():
    s = make_shelter(length=5.0, width=4.0, height=2.5, num_openings=2, opening_area_each=1.0)
    assert s.floor_area == pytest.approx(20.0)
    assert s.roof_area == pytest.approx(20.0)
    assert s.gross_wall_area == pytest.approx(2 * (5.0 + 4.0) * 2.5)
    assert s.total_opening_area == pytest.approx(2.0)
    assert s.net_wall_area == pytest.approx(s.gross_wall_area - 2.0)
    assert s.volume == pytest.approx(5.0 * 4.0 * 2.5)


def test_shelter_solar_exposed_area_default_vs_override():
    s_default = make_shelter(solar_wall_fraction=0.2)
    expected = s_default.roof_area + 0.2 * s_default.net_wall_area
    assert s_default.solar_exposed_area == pytest.approx(expected)

    s_override = make_shelter(solar_exposed_area_override=99.0)
    assert s_override.solar_exposed_area == pytest.approx(99.0)


def test_shelter_rejects_negative_dimensions():
    with pytest.raises(ThermalEngineValidationError):
        make_shelter(length=-1.0)


def test_shelter_rejects_openings_larger_than_wall():
    with pytest.raises(ValueError):
        make_shelter(length=1.0, width=1.0, height=1.0, num_openings=1, opening_area_each=100.0)


def test_shelter_rejects_wrong_material_type():
    with pytest.raises(TypeError):
        make_shelter(wall_material="not a material")


def test_shelter_thermal_capacity_is_positive():
    s = make_shelter()
    assert s.thermal_capacity > 0


# --- Simulation execution ----------------------------------------------------


def test_simulate_shelter_constant_conditions_runs_and_has_expected_columns():
    s = make_shelter()
    result = simulate_shelter(
        shelter=s,
        ambient_temperature=-10.0,
        solar_radiation=500.0,
        duration_hours=6,
        time_step_hours=1.0,
    )
    df = result.timeseries
    assert len(df) == 6
    expected_columns = {
        "time_hours",
        "ambient_temperature",
        "indoor_temperature",
        "solar_radiation",
        "solar_gain",
        "wall_heat_loss",
        "roof_heat_loss",
        "floor_heat_loss",
        "opening_heat_loss",
        "total_heat_loss",
        "net_heat_flow",
    }
    assert expected_columns.issubset(set(df.columns))


def test_simulate_shelter_time_series_conditions():
    s = make_shelter()
    ambient = [-10, -10, -9, -5, 0, 2, 3, 2, 0, -3, -6, -9] * 2  # 24 values
    solar = [0, 0, 0, 50, 200, 400, 600, 500, 200, 50, 0, 0] * 2  # 24 values
    result = simulate_shelter(
        shelter=s,
        ambient_temperature=ambient,
        solar_radiation=solar,
        duration_hours=24,
        time_step_hours=1.0,
    )
    assert len(result.timeseries) == 24
    assert result.timeseries["ambient_temperature"].iloc[3] == pytest.approx(-5)


def test_simulate_shelter_resamples_mismatched_series_length():
    s = make_shelter()
    ambient_24 = list(range(24))  # 24 hourly values
    solar_24 = [0] * 24
    # Run with a 30-minute timestep over 24h -> 48 steps, different from
    # the 24-length input series; engine should resample instead of erroring.
    result = simulate_shelter(
        shelter=s,
        ambient_temperature=ambient_24,
        solar_radiation=solar_24,
        duration_hours=24,
        time_step_hours=0.5,
    )
    assert len(result.timeseries) == 48


def test_indoor_temperature_changes_over_time_with_cold_ambient():
    s = make_shelter(initial_indoor_temperature=20.0)
    result = simulate_shelter(
        shelter=s,
        ambient_temperature=-20.0,
        solar_radiation=0.0,
        duration_hours=12,
        time_step_hours=1.0,
    )
    temps = result.timeseries["indoor_temperature"]
    # With no solar gain and a much colder ambient temperature, the shelter
    # should be losing heat throughout, so indoor temperature should be
    # monotonically non-increasing, and end colder than it started.
    assert temps.iloc[-1] < temps.iloc[0]
    assert all(t2 <= t1 + 1e-9 for t1, t2 in zip(temps, temps.iloc[1:]))


def test_indoor_temperature_moves_toward_hot_ambient():
    s = make_shelter(initial_indoor_temperature=0.0)
    result = simulate_shelter(
        shelter=s,
        ambient_temperature=40.0,
        solar_radiation=0.0,
        duration_hours=12,
        time_step_hours=1.0,
    )
    temps = result.timeseries["indoor_temperature"]
    assert temps.iloc[-1] > temps.iloc[0]


def test_simulate_shelter_summary_metrics_and_comfort_range():
    s = make_shelter(initial_indoor_temperature=18.0)
    result = simulate_shelter(
        shelter=s,
        ambient_temperature=17.0,
        solar_radiation=100.0,
        duration_hours=5,
        time_step_hours=1.0,
        comfort_range=(15.0, 25.0),
    )
    summary = result.summary
    assert summary["minimum_indoor_temperature"] <= summary["average_indoor_temperature"]
    assert summary["average_indoor_temperature"] <= summary["maximum_indoor_temperature"]
    assert summary["fraction_time_in_comfort"] == pytest.approx(1.0)
    assert summary["time_in_comfort_hours"] == pytest.approx(5.0)


def test_simulate_shelter_rejects_invalid_duration_or_timestep():
    s = make_shelter()
    with pytest.raises(ThermalEngineValidationError):
        simulate_shelter(s, ambient_temperature=0.0, solar_radiation=0.0, duration_hours=-5)
    with pytest.raises(ValueError):
        simulate_shelter(
            s, ambient_temperature=0.0, solar_radiation=0.0, duration_hours=1, time_step_hours=5
        )


def test_simulate_shelter_rejects_negative_solar_radiation():
    s = make_shelter()
    with pytest.raises(ThermalEngineValidationError):
        simulate_shelter(s, ambient_temperature=0.0, solar_radiation=-100.0, duration_hours=1)


# --- Multi-design comparison -------------------------------------------------


def test_compare_designs_returns_one_row_per_design_sorted_by_temperature():
    insulated = Material(
        name="Insulated Wall",
        thermal_conductivity=0.05,
        density=200.0,
        specific_heat=900.0,
        thickness=0.2,
        solar_absorptivity=0.5,
    )
    design_cold = make_shelter(name="Uninsulated", wall_material=EXAMPLE_MATERIALS["cgi_sheet_roof"])
    design_warm = make_shelter(name="Insulated", wall_material=insulated)

    comparison = compare_designs(
        designs={"cold_design": design_cold, "warm_design": design_warm},
        ambient_temperature=-15.0,
        solar_radiation=0.0,
        duration_hours=24,
        time_step_hours=1.0,
        comfort_range=(15.0, 24.0),
    )

    assert len(comparison) == 2
    assert set(comparison.index) == {"cold_design", "warm_design"}
    # Better-insulated design should retain heat better -> higher average
    # indoor temperature -> should be sorted first.
    assert comparison.index[0] == "warm_design"
    assert (
        comparison.loc["warm_design", "average_indoor_temperature"]
        > comparison.loc["cold_design", "average_indoor_temperature"]
    )


def test_compare_designs_rejects_empty_dict():
    with pytest.raises(ValueError):
        compare_designs(
            designs={},
            ambient_temperature=0.0,
            solar_radiation=0.0,
            duration_hours=1,
        )
