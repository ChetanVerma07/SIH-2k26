"""Optional plotting utilities (matplotlib). Kept separate from provider/
processing logic so the module can be used headlessly (e.g. in the API)
without requiring a display backend or matplotlib at all call sites.
"""
from __future__ import annotations
from typing import List, Optional

from weather_module.models.weather import WeatherObservation


def _require_matplotlib():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        return plt
    except ImportError as e:
        raise ImportError(
            "matplotlib is required for plotting utilities. Install with "
            "`pip install matplotlib`."
        ) from e


def _series(observations: List[WeatherObservation], field: str):
    times = [o.timestamp for o in observations]
    values = [getattr(o, field) for o in observations]
    return times, values


def plot_temperature(observations: List[WeatherObservation], out_path: str) -> str:
    plt = _require_matplotlib()
    t, v = _series(observations, "temperature_c")
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(t, v, color="tab:red", marker="o", markersize=3)
    ax.set_title("Temperature vs Time")
    ax.set_xlabel("Time")
    ax.set_ylabel("Temperature (\u00b0C)")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def plot_solar_radiation(observations: List[WeatherObservation], out_path: str) -> str:
    plt = _require_matplotlib()
    t, v = _series(observations, "solar_radiation_wm2")
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(t, v, color="tab:orange", marker="o", markersize=3)
    ax.set_title("Solar Radiation vs Time")
    ax.set_xlabel("Time")
    ax.set_ylabel("Solar Radiation (W/m\u00b2)")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def plot_humidity(observations: List[WeatherObservation], out_path: str) -> str:
    plt = _require_matplotlib()
    t, v = _series(observations, "humidity_pct")
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(t, v, color="tab:blue", marker="o", markersize=3)
    ax.set_title("Humidity vs Time")
    ax.set_xlabel("Time")
    ax.set_ylabel("Relative Humidity (%)")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def plot_pressure(observations: List[WeatherObservation], out_path: str) -> str:
    plt = _require_matplotlib()
    t, v = _series(observations, "pressure_hpa")
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(t, v, color="tab:green", marker="o", markersize=3)
    ax.set_title("Pressure vs Time")
    ax.set_xlabel("Time")
    ax.set_ylabel("Pressure (hPa)")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def plot_overview(observations: List[WeatherObservation], out_path: str) -> str:
    plt = _require_matplotlib()
    t_temp, temp = _series(observations, "temperature_c")
    _, solar = _series(observations, "solar_radiation_wm2")
    _, hum = _series(observations, "humidity_pct")
    _, pres = _series(observations, "pressure_hpa")

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes[0, 0].plot(t_temp, temp, color="tab:red")
    axes[0, 0].set_title("Temperature (\u00b0C)")
    axes[0, 1].plot(t_temp, solar, color="tab:orange")
    axes[0, 1].set_title("Solar Radiation (W/m\u00b2)")
    axes[1, 0].plot(t_temp, hum, color="tab:blue")
    axes[1, 0].set_title("Humidity (%)")
    axes[1, 1].plot(t_temp, pres, color="tab:green")
    axes[1, 1].set_title("Pressure (hPa)")
    for ax in axes.flat:
        ax.set_xlabel("Time")
        ax.tick_params(axis="x", rotation=30)
    fig.suptitle("Weather Overview")
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    return out_path
