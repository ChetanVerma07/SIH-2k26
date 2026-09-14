from ansys_thermal.comparison import compare_designs, metrics_table
from ansys_thermal.models.simulation import SimulationConfig
from ansys_thermal.models.materials import get_example_material, MaterialAssignment


def test_compare_designs_runs_all_and_preserves_order(simple_geometry, simple_boundary_conditions):
    materials_a = MaterialAssignment(
        wall_material=get_example_material("rammed_earth"),
        roof_material=get_example_material("concrete_dense"),
        floor_material=get_example_material("concrete_dense"),
        window_material=get_example_material("single_glass"),
    )
    materials_b = MaterialAssignment(
        wall_material=get_example_material("aac_block"),
        roof_material=get_example_material("concrete_dense"),
        floor_material=get_example_material("concrete_dense"),
        window_material=get_example_material("double_glass"),
    )

    config_a = SimulationConfig(
        name="design_a", geometry=simple_geometry, materials=materials_a,
        boundary_conditions=simple_boundary_conditions,
    )
    config_b = SimulationConfig(
        name="design_b", geometry=simple_geometry, materials=materials_b,
        boundary_conditions=simple_boundary_conditions,
    )

    results = compare_designs([config_a, config_b])
    assert len(results) == 2
    assert results[0].design_name == "design_a"
    assert results[1].design_name == "design_b"

    for r in results:
        assert r.normalized_result["meta"]["is_mock"] is True


def test_metrics_table_has_expected_keys(simple_config):
    results = compare_designs([simple_config])
    table = metrics_table(results)
    assert len(table) == 1
    row = table[0]
    for key in (
        "design_name", "min_temp_c", "max_temp_c", "avg_temp_c",
        "total_heat_transfer_wh", "total_solar_gain_wh", "is_mock",
    ):
        assert key in row


def test_compare_designs_rejects_invalid_config(simple_geometry, simple_materials, simple_boundary_conditions):
    bad_geometry = simple_geometry
    bad_geometry.length = -5.0  # invalid
    bad_config = SimulationConfig(
        name="bad", geometry=bad_geometry, materials=simple_materials,
        boundary_conditions=simple_boundary_conditions,
    )
    import pytest
    from ansys_thermal.validation.validators import ValidationError
    with pytest.raises(ValidationError):
        compare_designs([bad_config])
