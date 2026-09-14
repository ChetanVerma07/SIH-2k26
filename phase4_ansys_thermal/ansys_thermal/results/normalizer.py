"""
Result normalization.

Converts raw parsed results (from either the mock adapter or, in
future, a real ANSYS post-processing export) into the common,
documented result schema used throughout the rest of the project:

{
  "meta": {
      "source": "mock" | "ansys",
      "name": str,
      "is_mock": bool,
      "warning": str | None
  },
  "summary": {
      "min_temp_c": float,
      "max_temp_c": float,
      "avg_temp_c": float,
      "total_heat_transfer_wh": float,
      "total_solar_gain_wh": float | None,
      "simulation_duration_hours": float
  },
  "time_series": [
      {"timestamp_hour": float, "indoor_temp_c": float,
       "ambient_temp_c": float, "heat_flow_w": float,
       "solar_gain_w": float | None}
      , ...
  ],
  "surface_results": {
      "wall_heat_transfer_wh": float,
      "roof_heat_transfer_wh": float,
      "floor_heat_transfer_wh": float,
      "opening_heat_transfer_wh": float
  },
  "spatial_results": {
      "min_temp_c": float | None,
      "max_temp_c": float | None,
      "avg_temp_c": float | None,
      "heat_flux_stats": dict | None
  }
}

`spatial_results` fields are `None` when not available (e.g. the mock
adapter only models a single lumped indoor node, so it cannot report
true spatial temperature/flux distribution — that requires an actual
ANSYS FE solve). This is intentional and documented, not an omission.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional


def _integrate_wh(time_series: List[Dict[str, Any]], field: str) -> float:
    """Trapezoidal integration of a power field (W) over hour
    timestamps to get energy in Wh."""
    if len(time_series) < 2:
        return 0.0
    total = 0.0
    for i in range(len(time_series) - 1):
        h0 = time_series[i]["hour"]
        h1 = time_series[i + 1]["hour"]
        v0 = time_series[i].get(field)
        v1 = time_series[i + 1].get(field)
        if v0 is None or v1 is None:
            continue
        total += 0.5 * (v0 + v1) * (h1 - h0)
    return total


def _integrate_surface_wh(time_series: List[Dict[str, Any]], surface: str) -> float:
    if len(time_series) < 2:
        return 0.0
    total = 0.0
    for i in range(len(time_series) - 1):
        h0 = time_series[i]["hour"]
        h1 = time_series[i + 1]["hour"]
        v0 = time_series[i].get("surface_heat_flow_w", {}).get(surface)
        v1 = time_series[i + 1].get("surface_heat_flow_w", {}).get(surface)
        if v0 is None or v1 is None:
            continue
        total += 0.5 * (v0 + v1) * (h1 - h0)
    return total


def normalize_result(
    raw: Dict[str, Any],
    source: str,
    name: str,
    is_mock: bool,
    warning: Optional[str] = None,
    spatial_results: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Normalize a raw result dict (as produced by result_parser) into
    the common documented schema.

    Parameters
    ----------
    raw: dict with a 'time_series' key (see result_parser docstring
        for the expected row schema).
    source: "mock" or "ansys" — recorded in meta, used to enforce that
        mock results are never silently presented as real ANSYS
        results.
    is_mock: must be True if and only if source == "mock".
    spatial_results: optional dict with min/max/avg temperature and
        heat flux statistics from an actual ANSYS FE solve. Left as
        None for the mock adapter (which has no spatial resolution).
    """
    if source not in ("mock", "ansys"):
        raise ValueError("source must be 'mock' or 'ansys'")
    if source == "mock" and not is_mock:
        raise ValueError("is_mock must be True when source == 'mock'")
    if source == "ansys" and is_mock:
        raise ValueError("is_mock must be False when source == 'ansys'")

    time_series_raw = raw.get("time_series", [])
    if not time_series_raw:
        raise ValueError("raw result has no time_series data to normalize")

    indoor_temps = [row["indoor_temp_c"] for row in time_series_raw]
    hours = [row["hour"] for row in time_series_raw]

    total_heat_wh = _integrate_wh(time_series_raw, "total_heat_flow_w")
    total_solar_wh = _integrate_wh(time_series_raw, "solar_gain_w")

    normalized_time_series = [
        {
            "timestamp_hour": row["hour"],
            "indoor_temp_c": row["indoor_temp_c"],
            "ambient_temp_c": row["ambient_temp_c"],
            "heat_flow_w": row["total_heat_flow_w"],
            "solar_gain_w": row.get("solar_gain_w"),
        }
        for row in time_series_raw
    ]

    surface_results = {
        "wall_heat_transfer_wh": round(_integrate_surface_wh(time_series_raw, "wall"), 3),
        "roof_heat_transfer_wh": round(_integrate_surface_wh(time_series_raw, "roof"), 3),
        "floor_heat_transfer_wh": round(_integrate_surface_wh(time_series_raw, "floor"), 3),
        "opening_heat_transfer_wh": round(
            _integrate_surface_wh(time_series_raw, "opening"), 3
        ),
    }

    normalized = {
        "meta": {
            "source": source,
            "name": name,
            "is_mock": is_mock,
            "warning": warning
            or (
                "MOCK SIMULATION — NOT ANSYS RESULT. Generated by the simplified "
                "lumped-parameter Python model, not by ANSYS."
                if is_mock
                else None
            ),
        },
        "summary": {
            "min_temp_c": round(min(indoor_temps), 4),
            "max_temp_c": round(max(indoor_temps), 4),
            "avg_temp_c": round(sum(indoor_temps) / len(indoor_temps), 4),
            "total_heat_transfer_wh": round(total_heat_wh, 3),
            "total_solar_gain_wh": round(total_solar_wh, 3) if total_solar_wh else 0.0,
            "simulation_duration_hours": round(max(hours) - min(hours), 4),
        },
        "time_series": normalized_time_series,
        "surface_results": surface_results,
        "spatial_results": spatial_results
        or {
            "min_temp_c": None,
            "max_temp_c": None,
            "avg_temp_c": None,
            "heat_flux_stats": None,
            "note": (
                "Spatial (element-by-element) temperature and heat-flux "
                "distribution is only available from an actual ANSYS FE "
                "solve. The mock adapter models a single lumped indoor "
                "air node and therefore has no spatial resolution."
            ),
        },
    }
    return normalized
