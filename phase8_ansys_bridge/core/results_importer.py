"""
Phase 8 - ANSYS results importer.

Reads the CSV produced by either backend (real ANSYS /POST26 *VWRITE
export, or MockANSYSBackend's synthesized run) into a simple, backend-
agnostic in-memory time series. Pure stdlib -- no pandas/numpy dependency.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass


@dataclass
class ThermalTimeSeries:
    time_s: list
    indoor_temp_c: list
    heat_flux_w_m2: list

    @property
    def time_h(self) -> list:
        return [t / 3600.0 for t in self.time_s]


def import_results(results_csv_path: str) -> ThermalTimeSeries:
    time_s, temps, flux = [], [], []
    with open(results_csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                time_s.append(float(row["time_s"]))
                temps.append(float(row["indoor_temp_c"]))
                flux.append(float(row["heat_flux_w_m2"]))
            except (KeyError, ValueError):
                continue  # skip malformed/comment rows

    if not time_s:
        raise ValueError(f"No usable rows found in results file: {results_csv_path}")

    return ThermalTimeSeries(time_s=time_s, indoor_temp_c=temps, heat_flux_w_m2=flux)
