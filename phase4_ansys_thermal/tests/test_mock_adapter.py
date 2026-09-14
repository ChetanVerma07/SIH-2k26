import pytest

from ansys_thermal.ansys.adapter import MockThermalAdapter


def test_mock_adapter_full_workflow(simple_config):
    adapter = MockThermalAdapter(simple_config)
    result = adapter.run_full_workflow()

    assert result["meta"]["is_mock"] is True
    assert result["meta"]["source"] == "mock"
    assert "MOCK" in result["meta"]["warning"]
    assert "NOT ANSYS RESULT" in result["meta"]["warning"]


def test_mock_adapter_stage_ordering_enforced(simple_config):
    adapter = MockThermalAdapter(simple_config)
    with pytest.raises(RuntimeError):
        adapter.apply_materials()  # prepare_model() not called yet


def test_mock_adapter_produces_time_series(simple_config):
    adapter = MockThermalAdapter(simple_config)
    result = adapter.run_full_workflow()
    ts = result["time_series"]
    assert len(ts) == len(simple_config.boundary_conditions.ambient_series)
    for row in ts:
        assert "indoor_temp_c" in row
        assert "ambient_temp_c" in row
        assert "heat_flow_w" in row


def test_mock_adapter_indoor_temp_responds_to_ambient(simple_geometry, simple_materials):
    """With a hot, high-solar constant ambient environment, the indoor
    temperature should trend upward from a cooler starting point."""
    from ansys_thermal.models.climate import BoundaryConditions, build_constant_climate
    from ansys_thermal.models.simulation import SimulationConfig

    series = build_constant_climate(
        ambient_temp_c=40.0, duration_hours=24.0, time_step_s=3600.0, solar_irradiance_w_m2=600.0
    )
    bc = BoundaryConditions(ambient_series=series, indoor_initial_temp_c=15.0, duration_hours=24.0)
    config = SimulationConfig(
        name="hot_test", geometry=simple_geometry, materials=simple_materials, boundary_conditions=bc
    )

    adapter = MockThermalAdapter(config)
    result = adapter.run_full_workflow()
    ts = result["time_series"]
    assert ts[-1]["indoor_temp_c"] > ts[0]["indoor_temp_c"]


def test_mock_adapter_summary_fields_present(simple_config):
    adapter = MockThermalAdapter(simple_config)
    result = adapter.run_full_workflow()
    summary = result["summary"]
    for key in (
        "min_temp_c",
        "max_temp_c",
        "avg_temp_c",
        "total_heat_transfer_wh",
        "total_solar_gain_wh",
        "simulation_duration_hours",
    ):
        assert key in summary


def test_mock_adapter_surface_results_present(simple_config):
    adapter = MockThermalAdapter(simple_config)
    result = adapter.run_full_workflow()
    sr = result["surface_results"]
    for key in (
        "wall_heat_transfer_wh",
        "roof_heat_transfer_wh",
        "floor_heat_transfer_wh",
        "opening_heat_transfer_wh",
    ):
        assert key in sr


def test_mock_adapter_spatial_results_documented_as_unavailable(simple_config):
    adapter = MockThermalAdapter(simple_config)
    result = adapter.run_full_workflow()
    spatial = result["spatial_results"]
    assert spatial["min_temp_c"] is None
    assert "note" in spatial
