"""
Phase 8 - End-to-end pipeline orchestrator.

Ties together: case creation -> ANSYS input generation -> backend run
(mock or real) -> results import -> metrics extraction -> simplified
model run -> comparison -> validation -> report generation.

This is the single entry point the rest of the project (or a CLI/demo)
should call. It is backend-agnostic: pass in any SimulationBackend.
"""

from __future__ import annotations

import os

from config import ShelterDesignParams, ClimateParams, SimulationSettings
from backend.simulation_backend import SimulationBackend, RunStatus
from backend.mock_backend import MockANSYSBackend
from core.case_manager import CaseManager
from core.results_importer import import_results
from core.metrics_extractor import extract_metrics
from core.simplified_thermal_model import run_simplified_model
from core.comparator import compare
from core.validator import validate
from core.report_generator import generate_report


class Phase8Pipeline:
    def __init__(self, backend: SimulationBackend = None,
                 cases_root: str = "simulation_cases"):
        self.backend = backend or MockANSYSBackend()
        self.case_manager = CaseManager(cases_root=cases_root)

    def run_case(self, design: ShelterDesignParams, climate: ClimateParams,
                 settings: SimulationSettings, case_id: str = None) -> dict:
        """Runs the full Phase 8 flow for one design/climate combination.
        Returns the final structured report dict. Also writes report.json
        and report.md into the case directory."""

        # keep settings.solver_backend metadata consistent with the actual
        # backend instance passed in
        case_id = self.case_manager.create_case(design, climate, settings, case_id)
        case_dir = self.case_manager.case_dir(case_id)

        # 1. Generate ANSYS-compatible input (always -- mock or real)
        input_file = self.backend.prepare_input(case_dir, design, climate, settings)
        self.case_manager.update_status(case_id, RunStatus.INPUT_READY,
                                         input_file=input_file,
                                         backend=self.backend.name)

        # 2. Run backend (mock synthesizes plausible data; real ANSYS solves)
        self.case_manager.update_status(case_id, RunStatus.RUNNING)
        run_result = self.backend.run(case_dir, input_file, settings)

        if run_result.status != RunStatus.COMPLETED:
            self.case_manager.update_status(
                case_id, RunStatus.FAILED,
                error_message=run_result.error_message,
                raw_log=run_result.raw_log,
            )
            return {
                "case_id": case_id,
                "status": "failed",
                "error_message": run_result.error_message,
                "input_file": input_file,
                "case_dir": case_dir,
            }

        self.case_manager.update_status(
            case_id, RunStatus.COMPLETED,
            results_file=run_result.results_file,
            wall_clock_s=run_result.wall_clock_s,
        )

        # 3. Import ANSYS (or mock) results
        ansys_series = import_results(run_result.results_file)

        # 4. Extract ANSYS-side thermal metrics
        envelope_area = design.wall_area_m2 + design.roof_area_m2
        ansys_metrics = extract_metrics(
            ansys_series, climate.ambient_temp_profile_c,
            settings.comfort_band_low_c, settings.comfort_band_high_c,
            envelope_area_m2=envelope_area,
        )

        # 5. Run the independent simplified model
        simplified_series = run_simplified_model(design, climate, settings)
        simplified_metrics = extract_metrics(
            simplified_series, climate.ambient_temp_profile_c,
            settings.comfort_band_low_c, settings.comfort_band_high_c,
            envelope_area_m2=envelope_area,
        )

        # 6. Compare
        comparison = compare(
            ansys_metrics, simplified_metrics,
            ansys_series, simplified_series,
            tolerance_pct=settings.deviation_tolerance_pct,
        )

        # 7. Validate design behaviour
        validation = validate(ansys_metrics, comparison, climate.climate_zone, settings)

        # 8. Structured report
        report = generate_report(
            case_dir, case_id, design, climate, settings, self.backend.name,
            ansys_metrics, simplified_metrics, comparison, validation,
        )

        report["status"] = "completed"
        report["case_dir"] = case_dir
        report["input_file"] = input_file
        return report
