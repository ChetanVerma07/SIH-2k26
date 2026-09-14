"""Solar radiation estimation.

When a provider does not supply measured solar radiation, this module
estimates global horizontal irradiance (GHI, W/m^2) from time of day,
date, location, and cloud cover using a simplified clear-sky model
(solar geometry) attenuated by cloud cover. This is a documented
approximation, NOT a measurement, and callers must label it ESTIMATED.

Model summary:
1. Compute solar declination and hour angle from date/time/longitude.
2. Compute solar elevation angle from latitude, declination, hour angle.
3. Estimate clear-sky GHI using a simple extraterrestrial-radiation x
   atmospheric-transmittance approximation (not a full radiative-transfer
   model).
4. Attenuate by cloud cover fraction.
"""
from __future__ import annotations
import math
from datetime import datetime

SOLAR_CONSTANT_WM2 = 1361.0  # W/m^2, mean extraterrestrial irradiance


def _day_of_year(dt: datetime) -> int:
    return dt.timetuple().tm_yday


def solar_declination_deg(dt: datetime) -> float:
    n = _day_of_year(dt)
    return 23.45 * math.sin(math.radians(360.0 / 365.0 * (n - 81)))


def hour_angle_deg(dt: datetime, longitude_deg: float) -> float:
    """Approximate solar hour angle, using local solar time.

    This uses a simplified longitude-based time correction (no
    equation-of-time correction) which is adequate for a passive-shelter
    thermal-estimation context.
    """
    utc_hour = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    solar_time = utc_hour + (longitude_deg / 15.0)
    return 15.0 * (solar_time - 12.0)


def solar_elevation_deg(dt: datetime, latitude_deg: float, longitude_deg: float) -> float:
    decl = math.radians(solar_declination_deg(dt))
    lat = math.radians(latitude_deg)
    ha = math.radians(hour_angle_deg(dt, longitude_deg))
    sin_elev = (
        math.sin(lat) * math.sin(decl)
        + math.cos(lat) * math.cos(decl) * math.cos(ha)
    )
    sin_elev = max(-1.0, min(1.0, sin_elev))
    return math.degrees(math.asin(sin_elev))


def estimate_clear_sky_ghi_wm2(dt: datetime, latitude_deg: float, longitude_deg: float) -> float:
    """Simplified clear-sky global horizontal irradiance estimate."""
    elevation = solar_elevation_deg(dt, latitude_deg, longitude_deg)
    if elevation <= 0:
        return 0.0
    zenith_rad = math.radians(90.0 - elevation)
    # Simplified atmospheric transmittance (Kasten-type approximation)
    air_mass = 1.0 / max(math.cos(zenith_rad), 0.01)
    transmittance = 0.7 ** (air_mass ** 0.678)
    ghi = SOLAR_CONSTANT_WM2 * math.sin(math.radians(elevation)) * transmittance
    return max(0.0, ghi)


def estimate_solar_radiation_wm2(
    dt: datetime,
    latitude_deg: float,
    longitude_deg: float,
    cloud_cover_pct: float = 0.0,
) -> float:
    """Estimate GHI (W/m^2) attenuated by cloud cover.

    cloud_cover_pct: 0 (clear) to 100 (fully overcast).
    Attenuation follows a common empirical cloud-cover reduction curve.
    """
    clear_sky = estimate_clear_sky_ghi_wm2(dt, latitude_deg, longitude_deg)
    cloud_fraction = max(0.0, min(100.0, cloud_cover_pct)) / 100.0
    attenuation = 1.0 - 0.75 * (cloud_fraction ** 3.4)
    return round(max(0.0, clear_sky * attenuation), 2)
