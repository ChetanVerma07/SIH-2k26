#!/usr/bin/env python3
"""
Ladakh demonstration.

Runs the full Phase 4 workflow end-to-end for a cold, high-altitude
shelter scenario broadly representative of Ladakh's climate:

    1. Shelter creation (geometry)
    2. Material assignment
    3. Climate input (cold, high solar irradiance, large diurnal swing)
    4. Simulation setup (boundary conditions, validation)
    5. Mock execution (ANSYS is not required/available in this environment)
    6. Result extraction
    7. Result normalization
    8. Engineering summary + plots
    9. A small 3-design comparison (orientation variants)

Run with:
    python examples/ladakh_demo.py

This script uses ONLY the MockThermalAdapter. All printed/plotted
results are clearly labelled as mock. See README.md for how to adapt
this script to use AnsysThermalAdapter with a real ANSYS installation.

Climate values used here are DOCUMENTED, GENERIC approximations for a
cold high-altitude desert climate (broadly consistent with published
Ladakh climate descriptions: cold winters, large diurnal temperature
swings, high solar irradiance due to altitude and clear skies). They
are illustrative demonstration inputs, NOT site-measured meteorological
data. For a real design, replace with actual measured/forecast weather
data for the specific site.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running this script directly (`python examples/ladakh_demo.py`)
# without installing the package, by adding the project root to sys.path.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ansys_thermal.models.geometry import ShelterGeometry
from ansys_thermal.models.materials import MaterialAssignment, get_example_material
from ansys_thermal.models.climate import BoundaryConditions, build_diurnal_climate
from ansys_thermal.models.simulation import SimulationConfig
from ansys_thermal.validation.validators import validate_simulation_config
from ansys_thermal.ansys.adapter import MockThermalAdapter
from ansys_thermal.ansys import input_generator
from ansys_thermal.comparison import compare_designs, metrics_table
from ansys_thermal import visualization

GENERATED_DIR = PROJECT_ROOT / "generated" / "ladakh_demo"


def build_ladakh_config(orientation_deg: float = 180.0, wall_material_key: str = "rammed_earth", name_suffix: str = "") -> SimulationConfig:
    """Build a documented example configuration for a small passive
    shelter in a Ladakh-like cold, high-altitude climate."""

    # --- 1. Shelter creation (geometry) ---
    geometry = ShelterGeometry(
        length=6.0,
        width=4.0,
        height=2.8,
        wall_thickness=0.45,   # thick rammed-earth/brick wall, typical of cold-climate passive design
        roof_thickness=0.30,
        floor_thickness=0.20,
        window_area=2.5,       # south-facing glazing for passive solar gain
        door_area=1.8,
        other_openings_area=0.0,
        orientation_deg=orientation_deg,  # 180 = main facade facing South (Northern Hemisphere passive solar)
    )

    # --- 2. Material assignment ---
    materials = MaterialAssignment(
        wall_material=get_example_material(wall_material_key),
        roof_material=get_example_material("concrete_dense"),
        floor_material=get_example_material("concrete_dense"),
        window_material=get_example_material("double_glass"),
    )

    # --- 3. Climate input (documented generic Ladakh-like winter day) ---
    # Mean ambient ~ -5 degC, diurnal amplitude 10 degC (cold night ~ -15 degC,
    # daytime peak ~ +5 degC), peak solar irradiance 900 W/m^2 (high due to
    # altitude/clear skies), simulated over 48 hours at 1-hour steps.
    climate_series = build_diurnal_climate(
        mean_temp_c=-5.0,
        amplitude_c=10.0,
        duration_hours=48.0,
        time_step_s=3600.0,
        peak_hour=14.0,
        peak_solar_w_m2=900.0,
        sunrise_hour=7.0,
        sunset_hour=17.0,
    )

    boundary_conditions = BoundaryConditions(
        ambient_series=climate_series,
        indoor_initial_temp_c=10.0,
        internal_convection_w_m2k=8.0,
        external_convection_w_m2k=25.0,  # slightly higher: windy high-altitude exposure
        ground_temp_c=2.0,  # documented default assumption for partially frozen ground; replace with site data if available
        time_step_s=3600.0,
        duration_hours=48.0,
    )

    config = SimulationConfig(
        name=f"ladakh_passive_shelter{name_suffix}",
        geometry=geometry,
        materials=materials,
        boundary_conditions=boundary_conditions,
        notes=(
            "Illustrative cold high-altitude (Ladakh-like) passive shelter "
            "demonstration. Climate values are documented generic "
            "approximations, not site-measured data."
        ),
    )
    return config


def main() -> None:
    print("=" * 70)
    print("PHASE 4 DEMONSTRATION — Ladakh Passive Shelter Thermal Simulation")
    print("=" * 70)

    # --- 4. Simulation setup + validation ---
    config = build_ladakh_config()
    print(f"\n[1] Built simulation config: '{config.name}'")
    validate_simulation_config(config)
    print("[2] Configuration validated (geometry, materials, boundary conditions OK)")

    # Generate ANSYS-ready input artifacts regardless of adapter used.
    artifact_paths = input_generator.generate_all_inputs(config, GENERATED_DIR)
    print("[3] Generated ANSYS-ready input artifacts:")
    for label, path in artifact_paths.items():
        print(f"      - {label}: {path.relative_to(PROJECT_ROOT)}")

    # --- 5. Mock execution (ANSYS unavailable in this environment) ---
    print("\n[4] Running MOCK thermal simulation (no ANSYS installation required)...")
    adapter = MockThermalAdapter(config)
    result = adapter.run_full_workflow()

    print("\n" + "!" * 70)
    print(result["meta"]["warning"])
    print("!" * 70)

    # --- 6/7. Result extraction + normalization already done by adapter ---
    summary = result["summary"]
    print("\n[5] ENGINEERING SUMMARY (normalized result)")
    print(f"      Simulation duration       : {summary['simulation_duration_hours']} hours")
    print(f"      Minimum indoor temperature : {summary['min_temp_c']} degC")
    print(f"      Maximum indoor temperature : {summary['max_temp_c']} degC")
    print(f"      Average indoor temperature : {summary['avg_temp_c']} degC")
    print(f"      Total heat transfer        : {summary['total_heat_transfer_wh']} Wh")
    print(f"      Total solar gain           : {summary['total_solar_gain_wh']} Wh")

    sr = result["surface_results"]
    print("\n[6] SURFACE-LEVEL HEAT TRANSFER (Wh, + = heat gained by shelter)")
    print(f"      Walls    : {sr['wall_heat_transfer_wh']}")
    print(f"      Roof     : {sr['roof_heat_transfer_wh']}")
    print(f"      Floor    : {sr['floor_heat_transfer_wh']}")
    print(f"      Openings : {sr['opening_heat_transfer_wh']}")

    # --- 8. Plots ---
    print("\n[7] Generating engineering plots...")
    plot1 = visualization.plot_indoor_vs_ambient(result, GENERATED_DIR / "plot_indoor_vs_ambient.png")
    plot2 = visualization.plot_heat_flow_over_time(result, GENERATED_DIR / "plot_heat_flow.png")
    plot3 = visualization.plot_surface_heat_loss_comparison(result, GENERATED_DIR / "plot_surface_comparison.png")
    for p in (plot1, plot2, plot3):
        print(f"      - {p.relative_to(PROJECT_ROOT)}")

    # --- 9. Design comparison across orientations ---
    print("\n[8] Comparing 3 design variants (orientation + wall material)...")
    design_a = build_ladakh_config(orientation_deg=0.0, wall_material_key="rammed_earth", name_suffix="_A_north_rammedearth")
    design_b = build_ladakh_config(orientation_deg=90.0, wall_material_key="burnt_clay_brick", name_suffix="_B_east_brick")
    design_c = build_ladakh_config(orientation_deg=180.0, wall_material_key="aac_block", name_suffix="_C_south_aac")

    comparison_results = compare_designs([design_a, design_b, design_c])
    table = metrics_table(comparison_results)

    header = (
        f"{'Design':35s} {'Avg Temp(C)':>12s} {'Min(C)':>8s} {'Max(C)':>8s} "
        f"{'Total Heat(Wh)':>16s} {'Solar Gain(Wh)':>16s}"
    )
    print("\n      " + header)
    print("      " + "-" * len(header))
    for row in table:
        print(
            f"      {row['design_name']:35s} {row['avg_temp_c']:12.2f} "
            f"{row['min_temp_c']:8.2f} {row['max_temp_c']:8.2f} "
            f"{row['total_heat_transfer_wh']:16.1f} {row['total_solar_gain_wh']:16.1f}"
        )

    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE.")
    print(f"All generated artifacts are in: {GENERATED_DIR.relative_to(PROJECT_ROOT)}")
    print("Reminder: all numeric results above are from the MOCK adapter")
    print("(simplified lumped-parameter Python model) and are NOT validated")
    print("ANSYS results. See README.md for the real ANSYS integration path.")
    print("=" * 70)


if __name__ == "__main__":
    main()
