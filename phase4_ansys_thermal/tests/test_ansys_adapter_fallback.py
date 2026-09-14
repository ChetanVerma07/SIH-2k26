"""
Tests for AnsysThermalAdapter's graceful-failure behaviour on a system
without ANSYS / PyMAPDL installed. These tests must pass WITHOUT any
ANSYS installation, per the Phase 4 requirement that the whole test
suite runs without ANSYS.
"""

import pytest

from ansys_thermal.ansys.adapter import AnsysThermalAdapter, AnsysNotAvailableError


def test_ansys_adapter_prepare_model_generates_artifacts(simple_config, tmp_path):
    adapter = AnsysThermalAdapter(simple_config, generated_dir=tmp_path)
    adapter.prepare_model()
    assert (tmp_path / f"{simple_config.name}_config.json").exists()
    assert (tmp_path / f"{simple_config.name}_model.dat").exists()
    assert (tmp_path / f"{simple_config.name}_summary.txt").exists()


def test_ansys_adapter_execute_fails_gracefully_without_pymapdl(simple_config, tmp_path):
    adapter = AnsysThermalAdapter(simple_config, generated_dir=tmp_path)
    adapter.prepare_model()
    adapter.apply_materials()
    adapter.apply_boundary_conditions()
    adapter.configure_analysis()

    with pytest.raises(AnsysNotAvailableError):
        adapter.execute()


def test_ansys_adapter_stage_ordering_enforced(simple_config, tmp_path):
    adapter = AnsysThermalAdapter(simple_config, generated_dir=tmp_path)
    with pytest.raises(RuntimeError):
        adapter.apply_materials()  # prepare_model() not called yet


def test_ansys_adapter_extract_results_without_execution_raises(simple_config, tmp_path):
    adapter = AnsysThermalAdapter(simple_config, generated_dir=tmp_path)
    with pytest.raises(AnsysNotAvailableError):
        adapter.extract_results()


def test_ansys_adapter_extract_from_export_parses_real_results(simple_config, tmp_path):
    import json

    adapter = AnsysThermalAdapter(simple_config, generated_dir=tmp_path)
    result_file = tmp_path / "exported_result.json"
    result_file.write_text(
        json.dumps(
            {
                "meta": {},
                "time_series": [
                    {
                        "hour": 0,
                        "ambient_temp_c": 20.0,
                        "indoor_temp_c": 21.0,
                        "solar_irradiance_w_m2": 100.0,
                        "total_heat_flow_w": -10.0,
                        "solar_gain_w": 5.0,
                        "surface_heat_flow_w": {"wall": -5.0, "roof": -2.0, "floor": -1.0, "opening": -2.0},
                    },
                    {
                        "hour": 1,
                        "ambient_temp_c": 21.0,
                        "indoor_temp_c": 21.2,
                        "solar_irradiance_w_m2": 150.0,
                        "total_heat_flow_w": -8.0,
                        "solar_gain_w": 7.0,
                        "surface_heat_flow_w": {"wall": -4.0, "roof": -1.5, "floor": -1.0, "opening": -1.5},
                    },
                ],
            }
        )
    )

    normalized = adapter.extract_results_from_export(result_file)
    assert normalized["meta"]["is_mock"] is False
    assert normalized["meta"]["source"] == "ansys"
    assert normalized["meta"]["warning"] is None
