"""
Phase 8 - End-to-end demo (no ANSYS installation required).

Run:
    python demo.py

Runs two sample cases:
  1. A baseline hot-dry-climate shelter (thin wall, no insulation)
  2. An improved version (thicker wall + added insulation + shading)

...through the full Phase 8 pipeline using MockANSYSBackend, and prints a
summary. Full reports (JSON + Markdown) are written under
simulation_cases/<case_id>/.

To point this at a real ANSYS install instead, swap the backend:

    from backend.ansys_backend import ANSYSBackend
    pipeline = Phase8Pipeline(backend=ANSYSBackend(exe_path="mapdl", num_cores=4))
"""

from __future__ import annotations

from config import (ShelterDesignParams, ClimateParams, SimulationSettings,
                     ClimateZone, SolverBackendType)
from backend.mock_backend import MockANSYSBackend
from pipeline import Phase8Pipeline


def make_hot_dry_climate() -> ClimateParams:
    return ClimateParams(
        location_name="Jaisalmer, Rajasthan (sample)",
        climate_zone=ClimateZone.HOT_DRY,
        ambient_temp_profile_c=[26, 25, 24, 23, 23, 24, 27, 30, 33, 36,
                                 39, 41, 43, 43, 42, 40, 37, 34, 31, 29,
                                 28, 27, 26, 26],
        solar_radiation_profile_w_m2=[0, 0, 0, 0, 0, 60, 180, 350, 550, 720,
                                       850, 920, 940, 900, 790, 620, 410, 190,
                                       40, 0, 0, 0, 0, 0],
        relative_humidity_pct=20.0,
        wind_speed_m_s=3.2,
        ground_temp_c=28.0,
        altitude_m=225.0,
        season="summer",
    )


def make_baseline_design() -> ShelterDesignParams:
    return ShelterDesignParams(
        design_id="baseline_hotdry_v1",
        wall_material="fired_brick",
        wall_thickness_m=0.115,       # thin single-brick wall
        wall_conductivity_w_mk=0.81,
        roof_material="rcc_slab",
        roof_thickness_m=0.12,
        roof_conductivity_w_mk=1.58,
        insulation_r_value_m2k_w=0.0,  # no added insulation
        wall_area_m2=90.0,
        roof_area_m2=45.0,
        floor_area_m2=45.0,
        window_area_m2=8.0,
        window_u_value_w_m2k=3.2,
        orientation_deg=180.0,
        thermal_mass_class="low",
        shading_coefficient=0.95,      # minimal shading
        ventilation_ach=1.5,
        num_occupants=4,
        internal_gains_w=300.0,
    )


def make_improved_design() -> ShelterDesignParams:
    return ShelterDesignParams(
        design_id="improved_hotdry_v2",
        wall_material="stabilized_mud_block",
        wall_thickness_m=0.30,        # thick, high-mass wall typical for hot-dry vernacular design
        wall_conductivity_w_mk=0.60,
        roof_material="rcc_slab_with_insulation",
        roof_thickness_m=0.15,
        roof_conductivity_w_mk=1.58,
        insulation_r_value_m2k_w=1.2,  # added roof/wall insulation
        wall_area_m2=90.0,
        roof_area_m2=45.0,
        floor_area_m2=45.0,
        window_area_m2=5.0,            # smaller, shaded openings
        window_u_value_w_m2k=2.0,
        orientation_deg=180.0,
        thermal_mass_class="high",
        shading_coefficient=0.55,       # deep overhangs / jaali shading
        ventilation_ach=0.8,            # controlled night-flush ventilation
        num_occupants=4,
        internal_gains_w=300.0,
    )


def print_summary(label: str, report: dict) -> None:
    print(f"\n{'=' * 70}")
    print(f"CASE: {label}  (id={report.get('case_id')})")
    print(f"{'=' * 70}")
    if report.get("status") != "completed":
        print(f"  FAILED: {report.get('error_message')}")
        print(f"  ANSYS input file still generated at: {report.get('input_file')}")
        return

    am = report["ansys_metrics"]
    val = report["validation"]
    print(f"  Backend used           : {report['backend_used']}")
    print(f"  Peak indoor temp (C)   : {am['peak_indoor_temp_c']}")
    print(f"  Indoor temp swing (C)  : {am['indoor_temp_swing_c']}")
    print(f"  Decrement factor       : {am['decrement_factor']}")
    print(f"  Thermal lag (hours)    : {am['thermal_lag_hours']}")
    print(f"  Comfort hours (%)      : {am['comfort_pct']}%")
    print(f"  Overall verdict        : {val['overall_verdict'].upper()}")
    print(f"  Report written to      : {report['case_dir']}/report.md")


def main():
    settings = SimulationSettings(
        duration_hours=24,
        time_step_s=900,
        solver_backend=SolverBackendType.MOCK,
        comfort_band_low_c=20.0,
        comfort_band_high_c=32.0,
        deviation_tolerance_pct=15.0,
    )

    climate = make_hot_dry_climate()
    pipeline = Phase8Pipeline(backend=MockANSYSBackend())

    baseline_report = pipeline.run_case(make_baseline_design(), climate, settings)
    print_summary("Baseline (thin wall, no insulation, minimal shading)", baseline_report)

    improved_report = pipeline.run_case(make_improved_design(), climate, settings)
    print_summary("Improved (thick high-mass wall, insulation, deep shading)", improved_report)

    print(f"\n{'=' * 70}")
    print("Both cases complete. Inspect simulation_cases/<case_id>/ for:")
    print("  - shelter_thermal.inp   (real ANSYS APDL batch input)")
    print("  - ansys_results.csv     (backend results, mock or real)")
    print("  - report.json / report.md (full structured validation report)")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
