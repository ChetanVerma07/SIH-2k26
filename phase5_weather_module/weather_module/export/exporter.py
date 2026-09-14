"""Export normalized weather/climate data to CSV and JSON.

Output is structured so downstream applications (e.g. a thermal
simulation engine) can consume it without needing any weather_module
internals.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path
from typing import List

from weather_module.models.weather import WeatherObservation


def export_json(observations: List[WeatherObservation], path: str, meta: dict = None) -> str:
    payload = {
        "meta": meta or {},
        "count": len(observations),
        "observations": [o.to_dict() for o in observations],
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)
    return path


def export_csv(observations: List[WeatherObservation], path: str) -> str:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fieldnames = WeatherObservation.field_names()
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for o in observations:
            row = o.to_dict()
            row.pop("field_quality", None)
            writer.writerow({k: row.get(k) for k in fieldnames})
    return path


def export_simulation_profile_json(profile: dict, path: str) -> str:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, default=str)
    return path
