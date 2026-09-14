import csv
import json
from pathlib import Path

import pytest

from ansys_thermal.results.normalizer import normalize_result
from ansys_thermal.ansys.result_parser import (
    parse_json_result_file,
    parse_csv_result_file,
    ResultParseError,
)


def _sample_raw_time_series():
    return [
        {
            "hour": 0,
            "ambient_temp_c": 20.0,
            "indoor_temp_c": 22.0,
            "solar_irradiance_w_m2": 100.0,
            "total_heat_flow_w": -50.0,
            "solar_gain_w": 30.0,
            "surface_heat_flow_w": {"wall": -20.0, "roof": -10.0, "floor": -5.0, "opening": -15.0},
        },
        {
            "hour": 1,
            "ambient_temp_c": 22.0,
            "indoor_temp_c": 22.5,
            "solar_irradiance_w_m2": 200.0,
            "total_heat_flow_w": -30.0,
            "solar_gain_w": 60.0,
            "surface_heat_flow_w": {"wall": -10.0, "roof": -5.0, "floor": -5.0, "opening": -10.0},
        },
    ]


def test_normalize_result_mock_requires_is_mock_true():
    raw = {"time_series": _sample_raw_time_series()}
    with pytest.raises(ValueError):
        normalize_result(raw, source="mock", name="x", is_mock=False)


def test_normalize_result_ansys_requires_is_mock_false():
    raw = {"time_series": _sample_raw_time_series()}
    with pytest.raises(ValueError):
        normalize_result(raw, source="ansys", name="x", is_mock=True)


def test_normalize_result_basic_fields():
    raw = {"time_series": _sample_raw_time_series()}
    result = normalize_result(raw, source="mock", name="x", is_mock=True)
    assert result["summary"]["min_temp_c"] == 22.0
    assert result["summary"]["max_temp_c"] == 22.5
    assert result["meta"]["is_mock"] is True
    assert result["meta"]["warning"] is not None


def test_normalize_result_ansys_no_warning_by_default():
    raw = {"time_series": _sample_raw_time_series()}
    result = normalize_result(raw, source="ansys", name="x", is_mock=False)
    assert result["meta"]["warning"] is None


def test_normalize_result_empty_time_series_rejected():
    with pytest.raises(ValueError):
        normalize_result({"time_series": []}, source="mock", name="x", is_mock=True)


def test_parse_json_result_file(tmp_path):
    data = {"meta": {}, "time_series": _sample_raw_time_series()}
    path = tmp_path / "result.json"
    path.write_text(json.dumps(data))
    parsed = parse_json_result_file(path)
    assert len(parsed["time_series"]) == 2


def test_parse_json_result_file_missing_key_raises(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"foo": "bar"}))
    with pytest.raises(ResultParseError):
        parse_json_result_file(path)


def test_parse_json_result_file_missing_field_raises(tmp_path):
    bad_series = [{"hour": 0, "ambient_temp_c": 20.0}]  # missing required fields
    path = tmp_path / "bad2.json"
    path.write_text(json.dumps({"time_series": bad_series}))
    with pytest.raises(ResultParseError):
        parse_json_result_file(path)


def test_parse_json_result_file_missing_file_raises(tmp_path):
    with pytest.raises(ResultParseError):
        parse_json_result_file(tmp_path / "does_not_exist.json")


def test_parse_csv_result_file(tmp_path):
    path = tmp_path / "result.csv"
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "hour",
                "ambient_temp_c",
                "indoor_temp_c",
                "solar_irradiance_w_m2",
                "total_heat_flow_w",
                "solar_gain_w",
                "wall_heat_w",
                "roof_heat_w",
                "floor_heat_w",
                "opening_heat_w",
            ]
        )
        writer.writerow([0, 20.0, 22.0, 100.0, -50.0, 30.0, -20.0, -10.0, -5.0, -15.0])
        writer.writerow([1, 22.0, 22.5, 200.0, -30.0, 60.0, -10.0, -5.0, -5.0, -10.0])

    parsed = parse_csv_result_file(path)
    assert len(parsed["time_series"]) == 2
    assert parsed["time_series"][0]["surface_heat_flow_w"]["wall"] == -20.0


def test_parse_csv_result_file_missing_column_raises(tmp_path):
    path = tmp_path / "bad.csv"
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["hour", "ambient_temp_c"])  # missing most required columns
        writer.writerow([0, 20.0])
    with pytest.raises(ResultParseError):
        parse_csv_result_file(path)


def test_normalize_from_parsed_csv_end_to_end(tmp_path):
    path = tmp_path / "result.csv"
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "hour", "ambient_temp_c", "indoor_temp_c", "solar_irradiance_w_m2",
                "total_heat_flow_w", "solar_gain_w", "wall_heat_w", "roof_heat_w",
                "floor_heat_w", "opening_heat_w",
            ]
        )
        writer.writerow([0, 20.0, 22.0, 100.0, -50.0, 30.0, -20.0, -10.0, -5.0, -15.0])
        writer.writerow([1, 22.0, 22.5, 200.0, -30.0, 60.0, -10.0, -5.0, -5.0, -10.0])

    parsed = parse_csv_result_file(path)
    normalized = normalize_result(parsed, source="ansys", name="csv_test", is_mock=False)
    assert normalized["summary"]["max_temp_c"] == 22.5
    assert normalized["meta"]["source"] == "ansys"
