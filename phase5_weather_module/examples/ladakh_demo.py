"""Ladakh demo: end-to-end demonstration of the Phase 5 weather module.

Run with:
    python examples/ladakh_demo.py

Works fully offline (mock provider) — no API key required.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from weather_module.providers.mock import MockWeatherProvider
from weather_module.services.weather_service import WeatherService
from weather_module.export.exporter import export_csv, export_json, export_simulation_profile_json
from weather_module.processing.validator import validate_series
from weather_module.models.weather import WeatherObservation, QualityFlag


def _reconstruct_observations(profile: dict):
    """Rebuild WeatherObservation objects from the profile dict (for export/plots)."""
    from datetime import datetime
    obs_list = []
    for o in profile["observations"]:
        obs_list.append(WeatherObservation(
            timestamp=datetime.fromisoformat(o["timestamp"]),
            latitude=o["latitude"],
            longitude=o["longitude"],
            location_name=o["location_name"],
            temperature_c=o["temperature_c"],
            humidity_pct=o["humidity_pct"],
            pressure_hpa=o["pressure_hpa"],
            solar_radiation_wm2=o["solar_radiation_wm2"],
            wind_speed_ms=o["wind_speed_ms"],
            wind_direction_deg=o["wind_direction_deg"],
            cloud_cover_pct=o["cloud_cover_pct"],
            precipitation_mm=o["precipitation_mm"],
            quality=QualityFlag(o["quality"]),
            quality_reason=o["quality_reason"],
        ))
    return obs_list


def main():
    print("=" * 50)
    print("PHASE 5 WEATHER MODULE - LADAKH DEMO")
    print("=" * 50)

    service = WeatherService(provider=MockWeatherProvider())

    # 1 & 2: Load Ladakh demo provider + generate 24h profile
    profile = service.demo_ladakh_profile(interval_minutes=60)
    observations = _reconstruct_observations(profile)

    # 3: Validate
    stats = validate_series(observations)

    # 4: Quality statistics
    print(f"\nLOCATION: {profile['location']}")
    print("DATA SOURCE: MOCK / DEMO")
    print(f"\nObservations: {stats.total}")
    print(f"Valid: {stats.valid}")
    print(f"Suspect: {stats.suspect}")
    print(f"Corrected: {stats.corrected}")
    print(f"Missing: {stats.missing}")

    temps = [o.temperature_c for o in observations if o.temperature_c is not None]
    solar = [o.solar_radiation_wm2 for o in observations if o.solar_radiation_wm2 is not None]
    humidity = [o.humidity_pct for o in observations if o.humidity_pct is not None]

    print("\nTemperature:")
    print(f"Min: {min(temps):.1f} \u00b0C")
    print(f"Max: {max(temps):.1f} \u00b0C")

    print("\nSolar Radiation:")
    print(f"Peak: {max(solar):.1f} W/m\u00b2")

    print("\nHumidity:")
    print(f"Average: {sum(humidity) / len(humidity):.1f} %")

    # 5 & 6: Export CSV and JSON
    data_dir = Path(__file__).resolve().parent.parent / "data"
    csv_path = export_csv(observations, str(data_dir / "climate_profile.csv"))
    json_path = export_simulation_profile_json(profile, str(data_dir / "climate_profile.json"))

    # 7: Generate plots (best-effort; skip cleanly if matplotlib unavailable)
    plot_files = []
    try:
        from weather_module.processing.plotting import (
            plot_temperature, plot_solar_radiation, plot_humidity, plot_pressure, plot_overview,
        )
        plot_files.append(plot_temperature(observations, str(data_dir / "plot_temperature.png")))
        plot_files.append(plot_solar_radiation(observations, str(data_dir / "plot_solar.png")))
        plot_files.append(plot_humidity(observations, str(data_dir / "plot_humidity.png")))
        plot_files.append(plot_pressure(observations, str(data_dir / "plot_pressure.png")))
        plot_files.append(plot_overview(observations, str(data_dir / "plot_overview.png")))
    except ImportError:
        print("\n(matplotlib not installed - skipping plots)")

    # 8: Summary
    print("\nFiles generated:")
    print(f"{Path(csv_path).name}")
    print(f"{Path(json_path).name}")
    for p in plot_files:
        print(f"{Path(p).name}")

    print("\n" + "=" * 50)
    print("DEMO COMPLETE")
    print("=" * 50)


if __name__ == "__main__":
    main()
