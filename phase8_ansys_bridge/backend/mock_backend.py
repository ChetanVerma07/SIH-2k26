"""
Phase 8 - MockANSYSBackend.

Lets the whole pipeline (input generation -> run -> import -> metrics ->
compare -> validate -> report) be demonstrated and tested with zero
dependency on an ANSYS install or license.

It still writes a REAL, hand-off-ready APDL (.inp) file via
core.input_generator, so the artifact you'd actually submit to ANSYS is
identical to what the real backend would produce. Only the "run" step is
synthetic.

Design fidelity: the synthetic run is NOT a fixed canned curve -- it is
derived from the same envelope-physics helpers (UA, thermal capacitance,
solar gain) as the simplified model, so improving a design (more
insulation, more mass, better shading) visibly improves the "ANSYS"
numbers too. On top of that shared physics, a small independent
perturbation (thermal-bridging correction + light stochastic noise) is
applied so the mock run agrees with -- but never exactly matches -- the
simplified model, the way a real 3D ANSYS solve and a 1-node lumped model
never match exactly either. That gap is exactly what the comparator is
meant to check is within tolerance.
"""

from __future__ import annotations

import csv
import json
import math
import os
import random
import time

from backend.simulation_backend import SimulationBackend, BackendRunResult, RunStatus
from core.input_generator import generate_apdl_input
from core.envelope_physics import envelope_ua, thermal_capacitance, solar_gain_params
from config import ShelterDesignParams


class MockANSYSBackend(SimulationBackend):
    name = "mock_ansys"

    def __init__(self, seed: int = 42, thermal_bridging_pct: float = 8.0):
        self._seed = seed
        # Extra UA fraction to emulate 3D conduction paths (corners, thermal
        # bridges) that a 1-node lumped model doesn't see but a real 3D
        # ANSYS solve would pick up.
        self._thermal_bridging_pct = thermal_bridging_pct

    def is_available(self) -> bool:
        # Always available -- that's the point of the mock backend.
        return True

    def prepare_input(self, case_dir: str, design, climate, settings) -> str:
        return generate_apdl_input(case_dir, design, climate, settings)

    def run(self, case_dir: str, input_file: str, settings) -> BackendRunResult:
        start = time.time()

        try:
            design = self._load_design(case_dir)
            hourly_ambient, hourly_solar = self._load_profile(case_dir)

            # deterministic-but-case-specific noise: seed off the case dir
            # name so different cases don't produce identical noise, while
            # a given case is still reproducible across repeated runs.
            rng = random.Random(f"{self._seed}:{os.path.basename(case_dir.rstrip(os.sep))}")

            ua = envelope_ua(design) * (1.0 + self._thermal_bridging_pct / 100.0)
            capacitance = thermal_capacitance(design) * (1.0 + rng.uniform(-0.05, 0.05))
            solar_absorptance, effective_solar_area = solar_gain_params(design)

            dt = settings.time_step_s
            n_steps = int(settings.duration_hours * 3600 / dt) + 1

            results_path = os.path.join(case_dir, "ansys_results.csv")
            with open(results_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["time_s", "indoor_temp_c", "heat_flux_w_m2"])

                indoor_temp = hourly_ambient[0]
                envelope_area = max(design.wall_area_m2 + design.roof_area_m2, 1.0)

                for step in range(n_steps):
                    t_s = step * dt
                    t_h = t_s / 3600.0
                    hour_idx = int(t_h) % 24
                    next_idx = (hour_idx + 1) % 24
                    frac = t_h - int(t_h)

                    ambient = (hourly_ambient[hour_idx] * (1 - frac)
                               + hourly_ambient[next_idx] * frac)
                    solar = (hourly_solar[hour_idx] * (1 - frac)
                             + hourly_solar[next_idx] * frac)

                    q_solar = (solar_absorptance * effective_solar_area * solar
                               / design.wall_area_m2) if design.wall_area_m2 else 0.0
                    q_internal = design.internal_gains_w

                    # Analytic (unconditionally stable) update, same form as the
                    # simplified model -- see core/simplified_thermal_model.py.
                    k = ua / capacitance
                    t_equilibrium = ambient + (q_solar + q_internal) / ua if ua > 1e-9 else ambient
                    indoor_temp = t_equilibrium + (indoor_temp - t_equilibrium) * math.exp(-k * dt)
                    # small sensor/solver noise, independent of the simplified model
                    indoor_temp += rng.uniform(-0.04, 0.04)

                    heat_flux = (ambient - indoor_temp) * ua / envelope_area

                    writer.writerow([f"{t_s:.1f}", f"{indoor_temp:.3f}", f"{heat_flux:.3f}"])

            elapsed = time.time() - start
            return BackendRunResult(
                status=RunStatus.COMPLETED,
                results_file=results_path,
                raw_log=(f"[MockANSYSBackend] synthesized {n_steps} timesteps "
                         f"for design '{design.design_id}' in {elapsed:.3f}s "
                         f"(UA={ua:.1f} W/K incl. {self._thermal_bridging_pct}% "
                         "thermal-bridging correction)"),
                wall_clock_s=elapsed,
            )
        except Exception as exc:  # pragma: no cover - defensive
            return BackendRunResult(
                status=RunStatus.FAILED,
                error_message=str(exc),
                wall_clock_s=time.time() - start,
            )

    # ------------------------------------------------------------------ #
    @staticmethod
    def _load_design(case_dir: str) -> ShelterDesignParams:
        case_json = os.path.join(case_dir, "case.json")
        with open(case_json) as f:
            meta = json.load(f)
        d = dict(meta["design"])
        return ShelterDesignParams(**d)

    @staticmethod
    def _load_profile(case_dir: str) -> tuple:
        profile_path = os.path.join(case_dir, "_mock_profile.csv")
        if not os.path.exists(profile_path):
            raise FileNotFoundError(
                "Mock backend requires the '_mock_profile.csv' side-channel "
                "written by CaseManager.create_case() before run() is called."
            )
        ambient, solar = [None] * 24, [None] * 24
        with open(profile_path, newline="") as pf:
            reader = csv.DictReader(pf)
            for row in reader:
                h = int(row["hour"]) % 24
                ambient[h] = float(row["ambient_c"])
                solar[h] = float(row["solar_w_m2"])
        return ambient, solar
