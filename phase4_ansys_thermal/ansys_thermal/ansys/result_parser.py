"""
Result parser.

Parses structured, DOCUMENTED intermediate result formats into a raw
Python dict that ``ansys_thermal.results.normalizer`` can then turn
into the common normalized result schema.

Two documented formats are supported:

1. JSON result format (produced by MockThermalAdapter, and the format
   a real ANSYS post-processing script SHOULD export to, e.g. via an
   APDL `*MWRITE`/Python `ansys.mapdl` results export, or a Mechanical
   scripting `Export` action written to JSON):

    {
      "meta": {"name": ..., "source": "mock" | "ansys", ...},
      "time_series": [
        {"hour": ..., "ambient_temp_c": ..., "indoor_temp_c": ...,
         "solar_irradiance_w_m2": ..., "total_heat_flow_w": ...,
         "solar_gain_w": ...,
         "surface_heat_flow_w": {"wall": ..., "roof": ..., "floor": ..., "opening": ...}}
        , ...
      ]
    }

2. CSV result format (documented columns):

    hour,ambient_temp_c,indoor_temp_c,solar_irradiance_w_m2,
    total_heat_flow_w,solar_gain_w,wall_heat_w,roof_heat_w,
    floor_heat_w,opening_heat_w

This parser does NOT depend on any undocumented/proprietary ANSYS
binary output format (e.g. .rst files are NOT parsed here). If a real
ANSYS workflow is used, its post-processing step is responsible for
exporting to one of these two documented formats first.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, Any, List


class ResultParseError(ValueError):
    """Raised when a result file does not match the documented schema."""


def parse_json_result_file(path: Path) -> Dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise ResultParseError(f"Result file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            raise ResultParseError(f"Invalid JSON in result file {path}: {exc}") from exc

    if "time_series" not in data:
        raise ResultParseError(
            f"Result file {path} is missing required 'time_series' key. "
            "Expected documented JSON result schema."
        )

    required_fields = {
        "hour",
        "ambient_temp_c",
        "indoor_temp_c",
        "solar_irradiance_w_m2",
        "total_heat_flow_w",
    }
    for i, row in enumerate(data["time_series"]):
        missing = required_fields - set(row.keys())
        if missing:
            raise ResultParseError(
                f"time_series[{i}] in {path} is missing required fields: {missing}"
            )

    return data


def parse_csv_result_file(path: Path, meta: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Parse the documented CSV result format into the same raw dict
    shape produced by ``parse_json_result_file``."""
    path = Path(path)
    if not path.exists():
        raise ResultParseError(f"Result file not found: {path}")

    required_columns = {
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
    }

    time_series: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ResultParseError(f"CSV result file {path} has no header row")
        missing = required_columns - set(reader.fieldnames)
        if missing:
            raise ResultParseError(
                f"CSV result file {path} is missing required columns: {missing}"
            )
        for row in reader:
            time_series.append(
                {
                    "hour": float(row["hour"]),
                    "ambient_temp_c": float(row["ambient_temp_c"]),
                    "indoor_temp_c": float(row["indoor_temp_c"]),
                    "solar_irradiance_w_m2": float(row["solar_irradiance_w_m2"]),
                    "total_heat_flow_w": float(row["total_heat_flow_w"]),
                    "solar_gain_w": float(row["solar_gain_w"]),
                    "surface_heat_flow_w": {
                        "wall": float(row["wall_heat_w"]),
                        "roof": float(row["roof_heat_w"]),
                        "floor": float(row["floor_heat_w"]),
                        "opening": float(row["opening_heat_w"]),
                    },
                }
            )

    return {"meta": meta or {}, "time_series": time_series}
