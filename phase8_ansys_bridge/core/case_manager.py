"""
Phase 8 - Simulation case management.

Every "case" = one (design, climate, settings) combination. Cases live as
plain folders on disk under a cases root -- no database required:

  simulation_cases/<case_id>/
      case.json              metadata + status (persisted after every step)
      shelter_thermal.inp    ANSYS APDL input (always generated)
      _mock_profile.csv      side-channel hourly profile (mock backend only)
      ansys_results.csv      raw results (mock or real)
      report.json / report.md  final validation report
"""

from __future__ import annotations

import csv
import json
import os
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from enum import Enum

from config import ShelterDesignParams, ClimateParams, SimulationSettings
from backend.simulation_backend import RunStatus


class CaseManager:
    def __init__(self, cases_root: str = "simulation_cases"):
        self.cases_root = cases_root
        os.makedirs(self.cases_root, exist_ok=True)

    # ---------------------------------------------------------------- #
    def create_case(self, design: ShelterDesignParams, climate: ClimateParams,
                     settings: SimulationSettings, case_id: str = None) -> str:
        case_id = case_id or f"case_{uuid.uuid4().hex[:8]}"
        case_dir = self._case_dir(case_id)
        os.makedirs(case_dir, exist_ok=True)

        meta = {
            "case_id": case_id,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "status": RunStatus.NOT_STARTED.value,
            "design": design.to_dict(),
            "climate": climate.to_dict(),
            "settings": settings.to_dict(),
        }
        self._write_meta(case_id, meta)

        # Write the mock-backend side-channel profile up front so either
        # backend can be swapped in without re-touching the case.
        profile_path = os.path.join(case_dir, "_mock_profile.csv")
        with open(profile_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["hour", "ambient_c", "solar_w_m2"])
            for h in range(24):
                writer.writerow([
                    h,
                    climate.ambient_temp_profile_c[h % len(climate.ambient_temp_profile_c)],
                    climate.solar_radiation_profile_w_m2[h % len(climate.solar_radiation_profile_w_m2)],
                ])

        return case_id

    def update_status(self, case_id: str, status: RunStatus, **extra) -> None:
        meta = self.get_case(case_id)
        meta["status"] = status.value
        meta["updated_utc"] = datetime.now(timezone.utc).isoformat()
        meta.update(extra)
        self._write_meta(case_id, meta)

    def get_case(self, case_id: str) -> dict:
        path = os.path.join(self._case_dir(case_id), "case.json")
        with open(path) as f:
            return json.load(f)

    def list_cases(self) -> list:
        if not os.path.isdir(self.cases_root):
            return []
        out = []
        for name in sorted(os.listdir(self.cases_root)):
            case_json = os.path.join(self.cases_root, name, "case.json")
            if os.path.isfile(case_json):
                with open(case_json) as f:
                    out.append(json.load(f))
        return out

    def case_dir(self, case_id: str) -> str:
        return self._case_dir(case_id)

    # ---------------------------------------------------------------- #
    def _case_dir(self, case_id: str) -> str:
        return os.path.join(self.cases_root, case_id)

    def _write_meta(self, case_id: str, meta: dict) -> None:
        path = os.path.join(self._case_dir(case_id), "case.json")
        with open(path, "w") as f:
            json.dump(meta, f, indent=2, default=str)
