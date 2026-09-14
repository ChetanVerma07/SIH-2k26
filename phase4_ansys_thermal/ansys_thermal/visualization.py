"""
Engineering visualization utilities.

Kept separate from the ANSYS adapter layer: these functions only
consume the normalized result dict (see
ansys_thermal.results.normalizer) and produce matplotlib figures. They
have no knowledge of whether the result came from the mock adapter or
real ANSYS — callers should title/label plots using
``result["meta"]["warning"]`` when it is not None, to make sure mock
plots are never confused with validated ANSYS output.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional

import matplotlib

matplotlib.use("Agg")  # headless-safe backend; caller can save figures to file
import matplotlib.pyplot as plt


def _mock_suffix(result: Dict[str, Any]) -> str:
    return " [MOCK — NOT ANSYS RESULT]" if result["meta"].get("is_mock") else ""


def plot_indoor_vs_ambient(result: Dict[str, Any], output_path: Path) -> Path:
    """Plot indoor vs ambient temperature over time."""
    ts = result["time_series"]
    hours = [p["timestamp_hour"] for p in ts]
    indoor = [p["indoor_temp_c"] for p in ts]
    ambient = [p["ambient_temp_c"] for p in ts]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(hours, indoor, label="Indoor temperature", linewidth=2)
    ax.plot(hours, ambient, label="Ambient temperature", linewidth=2, linestyle="--")
    ax.set_xlabel("Time (hours)")
    ax.set_ylabel("Temperature (°C)")
    ax.set_title(f"Indoor vs Ambient Temperature — {result['meta']['name']}{_mock_suffix(result)}")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def plot_heat_flow_over_time(result: Dict[str, Any], output_path: Path) -> Path:
    """Plot total heat flow (and solar gain, if available) over time."""
    ts = result["time_series"]
    hours = [p["timestamp_hour"] for p in ts]
    heat_flow = [p["heat_flow_w"] for p in ts]
    solar = [p.get("solar_gain_w") or 0.0 for p in ts]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(hours, heat_flow, label="Net heat flow into shelter (W)", linewidth=2)
    ax.plot(hours, solar, label="Solar gain (W)", linewidth=2, linestyle=":")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Time (hours)")
    ax.set_ylabel("Power (W)")
    ax.set_title(f"Heat Flow Over Time — {result['meta']['name']}{_mock_suffix(result)}")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def plot_surface_heat_loss_comparison(result: Dict[str, Any], output_path: Path) -> Path:
    """Bar chart comparing total heat transfer through each surface
    type (wall/roof/floor/opening)."""
    sr = result["surface_results"]
    labels = ["Wall", "Roof", "Floor", "Opening"]
    values = [
        sr["wall_heat_transfer_wh"],
        sr["roof_heat_transfer_wh"],
        sr["floor_heat_transfer_wh"],
        sr["opening_heat_transfer_wh"],
    ]

    fig, ax = plt.subplots(figsize=(7, 5))
    colors = ["#4C72B0", "#DD8452", "#55A868", "#C44E52"]
    ax.bar(labels, values, color=colors)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_ylabel("Total heat transfer (Wh)")
    ax.set_title(
        f"Surface Heat-Loss/Gain Comparison — {result['meta']['name']}{_mock_suffix(result)}"
    )
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path
