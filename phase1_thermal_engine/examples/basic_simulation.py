"""
examples/basic_simulation.py
=============================

Runnable demonstration of the thermal engine using a 24-hour, cold,
high-altitude environment loosely representative of a winter day in
Ladakh (example/illustrative values only -- not measured weather data).

Run with:

    python examples/basic_simulation.py

or, from the project root:

    python main.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running this file directly (``python examples/basic_simulation.py``)
# without installing the package first.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from thermal_engine import EXAMPLE_MATERIALS, Material, Shelter, compare_designs, simulate_shelter

# ---------------------------------------------------------------------------
# 1. Example 24-hour weather profile for a cold, high-altitude winter day.
#
# These are illustrative, hand-authored example values in the rough shape
# of a Ladakh-type winter day (very cold night, strong but short daytime
# solar radiation typical of high-altitude, low-humidity, clear-sky sites,
# large diurnal swing). They are NOT sourced from a weather API or
# measured station data -- see README for how real weather data would be
# plugged in during a later phase.
# ---------------------------------------------------------------------------

HOURLY_AMBIENT_TEMPERATURE_C = [
    -14, -15, -15, -16, -16, -15, -13, -9, -4, 0, 3, 5,
    6, 6, 5, 3, 0, -4, -8, -11, -12, -13, -14, -14,
]  # 24 values, hour 0 .. hour 23

HOURLY_SOLAR_RADIATION_WM2 = [
    0, 0, 0, 0, 0, 0, 50, 220, 450, 650, 800, 880,
    900, 860, 760, 580, 350, 120, 0, 0, 0, 0, 0, 0,
]  # 24 values, hour 0 .. hour 23

COMFORT_RANGE_C = (15.0, 24.0)


def build_designs() -> dict[str, Shelter]:
    """Build three example shelter designs sharing the same geometry."""

    common_geometry = dict(
        length=6.0,
        width=4.0,
        height=2.8,
        num_openings=2,
        opening_area_each=1.2,
        initial_indoor_temperature=5.0,
        comfort_range=COMFORT_RANGE_C,
    )

    # Design A: traditional single-leaf mud adobe walls, CGI roof, no
    # insulation. Represents a common uninsulated baseline.
    design_a = Shelter(
        name="Design A - Traditional Mud Adobe, CGI Roof",
        wall_material=EXAMPLE_MATERIALS["mud_adobe"],
        roof_material=EXAMPLE_MATERIALS["cgi_sheet_roof"],
        floor_material=EXAMPLE_MATERIALS["concrete"],
        opening_u_value=5.7,  # single-glazed window, typical U-value
        **common_geometry,
    )

    # Design B: thick rammed-earth walls (higher thermal mass) with a
    # timber + basic construction roof, double-glazed openings.
    design_b = Shelter(
        name="Design B - Rammed Earth, Timber Roof",
        wall_material=EXAMPLE_MATERIALS["rammed_earth"],
        roof_material=EXAMPLE_MATERIALS["timber_plank"],
        floor_material=EXAMPLE_MATERIALS["concrete"],
        opening_u_value=2.8,  # double-glazed window, typical U-value
        **common_geometry,
    )

    # Design C: insulated wall (brick leaf + rock-wool insulation combined
    # into a single "effective" material layer for this simplified single-
    # layer model) with insulated roof, double-glazed openings.
    #
    # NOTE: This Phase 1 engine models each surface as a single material
    # layer. A composite/insulated wall is approximated here as one
    # "effective" material whose properties are blended from its
    # components. This approximation, and how multi-layer walls would be
    # handled properly in a later phase, is documented in the README.
    insulated_wall = Material(
        name="Brick + Rock Wool Insulation (effective, 330mm)",
        thermal_conductivity=0.09,
        density=900.0,
        specific_heat=860.0,
        thickness=0.33,
        solar_absorptivity=0.55,
        emissivity=0.90,
    )
    insulated_roof = Material(
        name="Timber + EPS Insulation (effective, 120mm)",
        thermal_conductivity=0.055,
        density=300.0,
        specific_heat=1200.0,
        thickness=0.12,
        solar_absorptivity=0.50,
        emissivity=0.90,
    )
    design_c = Shelter(
        name="Design C - Insulated Wall + Insulated Roof",
        wall_material=insulated_wall,
        roof_material=insulated_roof,
        floor_material=EXAMPLE_MATERIALS["concrete"],
        opening_u_value=2.0,  # low-E double-glazed window
        **common_geometry,
    )

    return {
        "Design A (baseline mud adobe)": design_a,
        "Design B (rammed earth)": design_b,
        "Design C (insulated)": design_c,
    }


def print_single_run_report(label: str, shelter: Shelter) -> None:
    result = simulate_shelter(
        shelter=shelter,
        ambient_temperature=HOURLY_AMBIENT_TEMPERATURE_C,
        solar_radiation=HOURLY_SOLAR_RADIATION_WM2,
        duration_hours=24,
        time_step_hours=1.0,
        comfort_range=COMFORT_RANGE_C,
    )
    s = result.summary
    print(f"\n--- {label} ---")
    print(f"  Minimum indoor temperature : {s['minimum_indoor_temperature']:6.2f} C")
    print(f"  Maximum indoor temperature : {s['maximum_indoor_temperature']:6.2f} C")
    print(f"  Average indoor temperature : {s['average_indoor_temperature']:6.2f} C")
    print(f"  Total solar energy gained  : {s['total_solar_energy_wh']:9.1f} Wh")
    print(f"  Total heat lost            : {s['total_heat_loss_wh']:9.1f} Wh")
    print(f"  Net energy balance         : {s['net_energy_balance_wh']:9.1f} Wh")
    print(
        f"  Time within comfort range  : "
        f"{s['time_in_comfort_hours']:.1f} h "
        f"({s['fraction_time_in_comfort'] * 100:.1f}% of the day)"
    )


def main() -> None:
    print("=" * 70)
    print("Passive Shelter Thermal Engine - Phase 1 Demo")
    print("Scenario: cold, high-altitude winter day (Ladakh-like example data)")
    print("=" * 70)

    designs = build_designs()

    # 1. Single-design detailed report (Design A, the baseline).
    print_single_run_report(
        "Design A (baseline mud adobe) - detailed", designs["Design A (baseline mud adobe)"]
    )

    # 2. Multi-design comparison.
    print("\n" + "=" * 70)
    print("Comparing all three designs under identical conditions")
    print("=" * 70)

    comparison = compare_designs(
        designs=designs,
        ambient_temperature=HOURLY_AMBIENT_TEMPERATURE_C,
        solar_radiation=HOURLY_SOLAR_RADIATION_WM2,
        duration_hours=24,
        time_step_hours=1.0,
        comfort_range=COMFORT_RANGE_C,
    )

    with __import__("pandas").option_context(
        "display.float_format", "{:.2f}".format, "display.width", 120
    ):
        print(comparison[
            [
                "average_indoor_temperature",
                "minimum_indoor_temperature",
                "maximum_indoor_temperature",
                "total_heat_loss_wh",
                "total_solar_energy_wh",
                "time_in_comfort_hours",
            ]
        ])

    best_label = comparison.index[0]
    print(
        f"\nBest-performing design by average indoor temperature: '{best_label}' "
        f"({comparison.loc[best_label, 'average_indoor_temperature']:.2f} C average, "
        f"{comparison.loc[best_label, 'time_in_comfort_hours']:.1f} h in comfort range)."
    )
    print(
        "\nNote: 'best' here is judged purely on indoor temperature/comfort-hours "
        "for this cold-climate scenario. A real design decision should also weigh "
        "cost, material availability, buildability and embodied energy."
    )


if __name__ == "__main__":
    main()
