"""
Deterministic climate profile + sample climate-data seed.

Run with:
    python -m app.seed.seed_climate

Safe to run repeatedly: each ClimateProfile is upserted by its unique
`name`. A 24-hour sample dataset is only inserted for a profile the
first time it is created (checked via existing ClimateData rows), so
re-running never duplicates time-series rows either.

The values below are small, deterministic, illustrative sample
profiles for early development/testing -- they are NOT sourced from a
live weather API and are not certified meteorological records.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.database import get_session
from app.repositories.climate_repository import ClimateRepository

CLIMATE_PROFILES = [
    dict(
        name="Ladakh / High Altitude Cold",
        location="Leh, Ladakh, India",
        latitude=34.1526,
        longitude=77.5771,
        climate_type="COLD_HIGH_ALTITUDE",
        description="Cold, arid, high-altitude climate with large diurnal temperature swings and strong solar radiation.",
    ),
    dict(
        name="Hot & Dry",
        location="Jaisalmer, Rajasthan, India",
        latitude=26.9157,
        longitude=70.9083,
        climate_type="HOT_DRY",
        description="Hot, low-humidity desert climate with high daytime solar load.",
    ),
    dict(
        name="Warm & Humid",
        location="Chennai, Tamil Nadu, India",
        latitude=13.0827,
        longitude=80.2707,
        climate_type="WARM_HUMID",
        description="Warm, high-humidity coastal climate with small diurnal temperature range.",
    ),
    dict(
        name="Composite",
        location="Delhi, India",
        latitude=28.7041,
        longitude=77.1025,
        climate_type="COMPOSITE",
        description="Composite climate: hot summers, cold winters, and a monsoon season.",
    ),
]

# Deterministic 24-hour sample profile for Ladakh / High Altitude Cold.
# Index = hour of day (0-23). Values are illustrative, not measured data.
_LADAKH_HOURLY = [
    # (temperature C, humidity %, pressure hPa, solar_radiation W/m2, wind_speed m/s, wind_direction deg)
    (-10.5, 40, 640, 0, 1.5, 270),
    (-11.2, 42, 640, 0, 1.4, 265),
    (-11.8, 43, 640, 0, 1.3, 260),
    (-12.0, 44, 640, 0, 1.2, 255),
    (-11.6, 43, 640, 0, 1.3, 250),
    (-10.4, 41, 640, 40, 1.6, 245),
    (-8.0, 38, 641, 180, 2.0, 240),
    (-4.5, 34, 641, 380, 2.4, 235),
    (-0.8, 30, 641, 560, 2.8, 230),
    (2.6, 27, 641, 700, 3.0, 225),
    (5.3, 24, 642, 800, 3.2, 220),
    (7.1, 22, 642, 860, 3.3, 215),
    (8.0, 21, 642, 880, 3.4, 210),
    (7.8, 21, 642, 840, 3.3, 205),
    (6.5, 23, 641, 740, 3.1, 200),
    (4.2, 26, 641, 590, 2.9, 195),
    (1.0, 30, 641, 400, 2.6, 200),
    (-2.5, 34, 641, 200, 2.3, 210),
    (-5.8, 37, 640, 40, 2.0, 220),
    (-7.9, 39, 640, 0, 1.8, 230),
    (-8.9, 40, 640, 0, 1.7, 240),
    (-9.6, 41, 640, 0, 1.6, 250),
    (-10.1, 41, 640, 0, 1.5, 260),
    (-10.3, 40, 640, 0, 1.5, 265),
]


def _ladakh_sample_rows(base_date: datetime) -> list[dict]:
    rows = []
    for hour, (temp, hum, pres, solar, wind_spd, wind_dir) in enumerate(_LADAKH_HOURLY):
        rows.append(
            dict(
                timestamp=base_date + timedelta(hours=hour),
                temperature=temp,
                humidity=hum,
                pressure=pres,
                solar_radiation=solar,
                wind_speed=wind_spd,
                wind_direction=wind_dir,
            )
        )
    return rows


def run() -> None:
    with get_session() as session:
        repo = ClimateRepository(session)
        created, skipped = 0, 0

        for profile in CLIMATE_PROFILES:
            existing = repo.get_by_name(profile["name"])
            if existing:
                skipped += 1
                obj = existing
            else:
                obj = repo.create(**profile)
                created += 1

            if profile["name"] == "Ladakh / High Altitude Cold":
                existing_data = repo.get_climate_data(obj.id)
                if not existing_data:
                    base_date = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
                    repo.bulk_add_climate_data(obj.id, _ladakh_sample_rows(base_date))
                    print("Inserted 24-hour sample climate dataset for Ladakh / High Altitude Cold.")

        print(f"Climate profile seed complete: {created} created, {skipped} already present.")


if __name__ == "__main__":
    run()
