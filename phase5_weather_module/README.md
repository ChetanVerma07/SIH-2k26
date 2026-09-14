# Phase 5 — Weather & Climate Data Module

**Project:** AI-Based Software Model for Designing Energy-Efficient Passive Shelters
for Different Climatic Conditions (SIH 2026)

**Scope:** This is Phase 5 only — a completely independent, standalone Python module
that collects, processes, validates and exports weather/climate data for later
consumption by a thermal simulation system. It does not depend on any other phase,
frontend, ANSYS, or a database.

---

## 1. Why weather data is required

Passive shelter design (insulation choice, orientation, glazing, thermal mass) depends
entirely on the climate the shelter sits in. A thermal simulation needs realistic,
time-resolved inputs — temperature, solar radiation, humidity, pressure, wind — to
predict how a design will perform. This module is the data-supply layer for that
simulation: it does not simulate the shelter itself.

## 2. Architecture

```
weather_module/
├── models/        Location, WeatherObservation, QualityFlag, DataSource
├── providers/      WeatherProvider (abstract) + MockWeatherProvider
├── processing/     normalizer, validator, resampler, solar estimation,
│                    cache/rate-limiter, plotting
├── services/       WeatherService — the facade the rest of an app should use
└── export/         CSV / JSON exporters

api/main.py          FastAPI service exposing the module over HTTP
examples/ladakh_demo.py   End-to-end offline demo
tests/                pytest suite (fully offline)
data/                 Generated exports / plots land here
```

Layering: `providers` → `processing` (normalize/validate/resample) → `services`
(orchestration) → `api` / `examples` (consumers). Nothing outside `providers/`
touches provider-specific response formats — everything downstream only sees
`WeatherObservation`.

## 3. Weather provider abstraction

`weather_module/providers/base.py` defines the abstract `WeatherProvider` interface:

```python
class WeatherProvider(ABC):
    def get_current_weather(self, location) -> WeatherObservation: ...
    def get_forecast(self, location, hours, interval_minutes) -> list[WeatherObservation]: ...
    def get_historical_weather(self, location, start, end) -> list[WeatherObservation]: ...
```

`MockWeatherProvider` is the only implementation shipped in this phase (see
"Mock mode" below), so the whole system runs without API keys or internet access.
The interface is deliberately provider-agnostic so a real API adapter (e.g.
Open-Meteo, OpenWeatherMap) can be dropped in later without changing
`services/`, `api/`, or any downstream thermal-simulation code — see
"How to configure a real weather provider".

## 4. Data normalization

All observations are normalized to a single `WeatherObservation` structure using
SI units:

| Field | Unit |
|---|---|
| temperature_c | °C |
| humidity_pct | % (0–100) |
| pressure_hpa | hPa |
| solar_radiation_wm2 | W/m² |
| wind_speed_ms | m/s |
| wind_direction_deg | degrees (0=N, 90=E, 180=S, 270=W) |
| cloud_cover_pct | % (0–100) |
| precipitation_mm | mm (accumulated per interval) |

`processing/normalizer.py` provides conversion helpers (°F→°C, K→°C, Pa→hPa,
mph/km/h→m/s, kWh/m²→W/m²) for adapting future real-API responses into this format.

## 5. Quality control

`processing/validator.py` checks every observation for:

- missing values, duplicate timestamps, invalid coordinates
- impossible temperature / humidity / pressure values
- negative solar radiation
- unrealistic jumps between consecutive observations

Data is **never silently deleted**. Each observation gets an overall
`quality` flag (`VALID` / `MISSING` / `SUSPECT` / `CORRECTED`), a
`quality_reason`, and optional per-field detail in `field_quality`, e.g.:

```json
{"temperature_c": -12.4, "quality": "SUSPECT", "quality_reason": "Abrupt temperature change of -14.2°C since previous observation"}
```

Where a safe repair exists (e.g. humidity clamped to [0,100]) the value is
corrected and flagged `CORRECTED`; the original problem is always recorded.

## 6. Solar radiation handling

`processing/solar.py` estimates global horizontal irradiance from solar
geometry (declination, hour angle, elevation) and cloud cover when a provider
doesn't supply it directly. Every observation records
`solar_radiation_source` as `MEASURED`, `ESTIMATED`, `MOCK`, or
`INTERPOLATED` — estimated values are never presented as measured.

## 7. Historical data

`WeatherProvider.get_historical_weather(location, start, end)` accepts a
single date or a date range. `MockWeatherProvider` generates deterministic
(seeded) hourly data for any requested range so historical queries work fully
offline.

## 8. Simulation profile generation

`WeatherService.generate_simulation_profile(location, duration_hours, interval_minutes)`
pulls a forecast series, resamples it to the requested interval (15/30/60 min,
via linear interpolation in `processing/resampler.py`), validates it, and
returns a dict ready for a thermal simulation engine:

```json
{
  "location": "Ladakh",
  "duration_hours": 24,
  "interval_minutes": 60,
  "quality_summary": {"total": 24, "valid": 24, "missing": 0, "suspect": 0, "corrected": 0},
  "observations": [ { "timestamp": "...", "temperature_c": -10.2, "solar_radiation_wm2": 0.0, "...": "..." } ]
}
```

## 9. Export format

`export/exporter.py` writes:

- `export_csv(observations, path)` → flat CSV, one row per observation
- `export_json(observations, path, meta)` → `{"meta": {...}, "count": N, "observations": [...]}`
- `export_simulation_profile_json(profile, path)` → the full simulation-profile dict

Both formats use the same field names as `WeatherObservation`, so any
consumer can read them without knowing about this module's internals.

## 10. API usage

Run:

```bash
uvicorn api.main:app --reload
```

Endpoints:

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Liveness check |
| GET | `/api/weather/current?location=ladakh` (or `lat`/`lon`) | Current observation |
| GET | `/api/weather/forecast?location=delhi&hours=24&interval_minutes=60` | Forecast series |
| GET | `/api/weather/historical?location=delhi&start=2026-01-01&end=2026-01-02` | Historical series |
| POST | `/api/weather/profile` | Simulation-ready profile (JSON body, see below) |
| GET | `/api/weather/demo` | Offline Ladakh demo profile |

**Example request:**

```bash
curl -X POST http://127.0.0.1:8000/api/weather/profile \
  -H "Content-Type: application/json" \
  -d '{"location_name": "ladakh", "duration_hours": 24, "interval_minutes": 60}'
```

**Example response (truncated):**

```json
{
  "location": "Ladakh",
  "latitude": 34.1526,
  "longitude": 77.5771,
  "duration_hours": 24,
  "interval_minutes": 60,
  "provider": "mock",
  "quality_summary": {"total": 24, "valid": 24, "missing": 0, "suspect": 0, "corrected": 0},
  "observations": [
    {
      "timestamp": "2026-09-13T00:00:00+00:00",
      "latitude": 34.1526, "longitude": 77.5771, "location_name": "Ladakh",
      "temperature_c": 0.86, "humidity_pct": 32.09, "pressure_hpa": 650.69,
      "solar_radiation_wm2": 0.0, "wind_speed_ms": 4.13, "wind_direction_deg": 138.4,
      "cloud_cover_pct": 12.7, "precipitation_mm": 0.0,
      "solar_radiation_source": "ESTIMATED", "data_source": "MOCK",
      "quality": "VALID", "quality_reason": null
    }
  ]
}
```

Interactive docs are auto-generated at `http://127.0.0.1:8000/docs`.

## 11. Mock mode

`MockWeatherProvider` synthesizes deterministic weather using a diurnal
sinusoidal model seeded by location + date, so repeated calls for the same
day/location return identical data (useful for tests and reproducible demos).
Built-in presets: `ladakh`, `delhi`, `mumbai`. Any other location requires
explicit `latitude`/`longitude` since the mock provider has no real geocoder.
All mock output is labeled `data_source: "MOCK"`.

## 12. How to configure a real weather provider

1. Create `weather_module/providers/my_provider.py` implementing the
   `WeatherProvider` interface (`get_current_weather`, `get_forecast`,
   `get_historical_weather`, optionally `resolve_location` for geocoding).
2. Inside it, call the real API, then build `WeatherObservation` objects using
   `processing/normalizer.py` helpers to convert units into this module's SI
   standard. Set `data_source=DataSource.MEASURED` (or `FORECAST`) and
   `solar_radiation_source` accordingly.
3. Wrap the API call with `processing/cache.TTLCache` and
   `processing/cache.RateLimiter` to avoid unnecessary repeated requests.
4. Pass an instance to `WeatherService(provider=MyProvider(), fallback_provider=MockWeatherProvider())`
   in `api/main.py`. If the live provider raises a `ProviderError`, the
   service falls back to mock data — always still labeled `MOCK`, never
   silently presented as measured data.

Realistically-accessible candidate APIs to adapt (not wired in for this
phase, since it must run without any key): **Open-Meteo** (no API key
required, good for current/forecast/historical), **OpenWeatherMap** (API key
required, current/forecast; historical needs a paid tier), **NASA POWER**
(no key, strong for solar radiation / historical climate data, coarser time
resolution). Document any provider's rate limits and coverage gaps directly
in its adapter file.

## 13. Limitations

- `MockWeatherProvider` has no real geocoder — only the three built-in
  presets resolve from a name; other locations need explicit coordinates.
- The solar-radiation estimator is a simplified clear-sky/cloud-attenuation
  model, not a full radiative-transfer model — adequate for passive-shelter
  screening, not for precision solar-engineering work.
- The resampler uses linear interpolation, which can under-represent sharp
  weather transitions between widely-spaced source points.
- The cache/rate-limiter are in-process and in-memory only (no persistence,
  no multi-process sharing) — sufficient for this phase, not for a
  production multi-worker deployment.
- No live third-party API is wired in yet (by design, so the project needs
  no key); see §12 to add one.

## 14. Connecting to the thermal simulation system (future)

`WeatherService.generate_simulation_profile(...)` is the intended integration
point: a thermal simulation module can call it directly (in-process) or via
`POST /api/weather/profile` (over HTTP), and consume the returned
`observations` array — a flat, unit-labeled, quality-flagged time series with
no weather_module-specific types. The `data/climate_profile.csv` /
`.json` exports serve the same purpose for simulation tools that read files
rather than call an API directly.

---

## Installation

```bash
cd phase5_weather_module
pip install -r requirements.txt
```

## Run the API

```bash
uvicorn api.main:app --reload
# then open http://127.0.0.1:8000/docs
```

## Run the offline demo

```bash
python examples/ladakh_demo.py
```

Generates `data/climate_profile.csv`, `data/climate_profile.json`, and five
plot PNGs.

## Run tests

```bash
pytest
```

All 34 tests run fully offline (mock provider + FastAPI `TestClient`).
