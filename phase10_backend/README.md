# Phase 10 — Passive Shelter API (FastAPI Backend)

Standalone FastAPI backend/API layer for the **AI-Based Software Model for
Designing Energy-Efficient Passive Shelters for Different Climatic
Conditions** (SIH 2026). This phase is fully self-contained: no React
frontend, PostgreSQL, ANSYS, or external weather API is required to run it.

## 1. Purpose

This service exposes a clean REST API for the whole application:

- Projects, shelter designs, climate data, and materials as CRUD resources.
- A deterministic **mock thermal simulation** engine.
- A deterministic **mock optimization** engine that searches insulation /
  opening-percentage combinations and scores candidate designs.
- An explainable **recommendation** endpoint.
- Multi-design **comparison** and full **project reports** (JSON + Markdown).

All heavy engines (thermal physics, optimization, ANSYS) sit behind small
interfaces so they can be swapped for real implementations later without
touching any route.

## 2. Architecture

```
Frontend (future)
   ↓
FastAPI (app/api/routes/*)
   ↓
Service layer (app/services/*)   ← all business logic lives here
   ↓
Thermal Engine / Optimizer / Simulation Backend (mocked) / In-memory repository
```

Routes never contain business logic — they only validate input (via
Pydantic) and call a service. Services never touch the HTTP layer.

## 3. API structure

Base prefix: `/api/v1`

| Resource | Prefix |
|---|---|
| Health | `/api/v1/health` |
| Projects | `/api/v1/projects` |
| Designs | `/api/v1/designs` |
| Climate | `/api/v1/climate` |
| Materials | `/api/v1/materials` |
| Simulations | `/api/v1/simulations` |
| Optimization | `/api/v1/optimization` |
| Recommendation | `/api/v1/projects/{project_id}/recommendation` |
| Comparisons | `/api/v1/comparisons` |
| Reports | `/api/v1/projects/{project_id}/report` (+ `/markdown`) |

Interactive docs: `http://localhost:8000/docs` (Swagger) and `/redoc`.

## 4. Endpoints

### Health
- `GET /api/v1/health` → `{"status": "ok", "service": "passive-shelter-api", "version": "1.0.0"}`

### Projects
- `POST /api/v1/projects` — create (`name`, `location`, `description`)
- `GET /api/v1/projects` — list
- `GET /api/v1/projects/{project_id}` — detail
- `DELETE /api/v1/projects/{project_id}` — delete

### Designs
- `POST /api/v1/designs` — create (geometry + materials + requirements, see schema below)
- `GET /api/v1/designs` — list
- `GET /api/v1/designs/{design_id}` — detail
- `PUT /api/v1/designs/{design_id}` — partial update
- `DELETE /api/v1/designs/{design_id}` — delete

### Climate
- `GET /api/v1/climate/presets` — Ladakh, Hot and Dry, Warm and Humid, Composite
- `GET /api/v1/climate/{location}` — lookup by name
- `POST /api/v1/climate` — custom climate (optionally with `time_series`)

### Materials
- `GET /api/v1/materials?category=insulation` — list, optional category filter
- `GET /api/v1/materials/{material_id}` — detail
- `POST /api/v1/materials` — create custom material

### Simulations
- `POST /api/v1/simulations` — create (`project_id`, `design_id`, `climate_id`, `duration`, `timestep`)
- `POST /api/v1/simulations/{id}/run` — run the mock thermal engine
- `GET /api/v1/simulations/{id}` — status (`CREATED` / `RUNNING` / `COMPLETED` / `FAILED`)
- `GET /api/v1/simulations/{id}/results` — indoor/outdoor temp, heat loss, solar gain, comfort %, etc.

### Optimization
- `POST /api/v1/optimization` — create (`project_id`, `baseline_design_id`, `parameters`)
- `POST /api/v1/optimization/{id}/run?climate_location=Composite` — generate + score candidates
- `GET /api/v1/optimization/{id}` — status/results

### Recommendation
- `GET /api/v1/projects/{project_id}/recommendation?climate_location=Composite`
  Returns the best-scoring design among the project's designs, with a
  human-readable `explanation`, plus `assumptions` and `limitations`.

### Comparisons
- `POST /api/v1/comparisons` — `{"design_ids": [...]}`, returns comfort /
  heat loss / solar gain / energy requirement / overall score per design.

### Reports
- `GET /api/v1/projects/{project_id}/report` — full structured JSON report
- `GET /api/v1/projects/{project_id}/report/markdown` — Markdown report

## 5. Data models

Pydantic schemas live in `app/schemas/`, plain dataclass-style domain models
in `app/models/`. Key inputs:

**Design** — geometry (`length`, `width`, `height`, `wall_thickness`,
`roof_thickness`, `floor_thickness`, `insulation_thickness`,
`opening_percentage`, `orientation`), materials (`wall_material`,
`roof_material`, `floor_material`, `insulation_material` — material IDs),
requirements (`occupants`, `floor_area`, `target_min_temperature`,
`target_max_temperature`). All numeric fields are range-validated; orientation
must be one of `N/S/E/W/NE/NW/SE/SW`; `target_max_temperature` must exceed
`target_min_temperature`.

**Material** — `name`, `category`, `thermal_conductivity`, `density`,
`specific_heat`, `emissivity`, `solar_absorptivity`, `cost_factor` — all
physically constrained (e.g. conductivity > 0, emissivity in [0, 1]).

**Climate** — `temperature`, `humidity`, `pressure`, `solar_radiation`,
`wind_speed`, `wind_direction`, optional `time_series`.

## 6. Service layer

Every route delegates to a service in `app/services/`
(`project_service.py`, `design_service.py`, `climate_service.py`,
`material_service.py`, `simulation_service.py`, `optimization_service.py`,
`recommendation_service.py`, `comparison_service.py`, `report_service.py`).
Services depend on the shared `RepositoryRegistry`
(`app/repositories/memory_repository.py`), a set of in-memory
dict-backed stores — this is the seam that will later be replaced by
SQLAlchemy + PostgreSQL.

## 7. Thermal engine abstraction

`app/services/thermal_engine.py` defines `ThermalEngine` (`calculate`,
`simulate`, `get_results`) and `MockThermalEngine`, a deterministic model
that is qualitatively physically sensible:

- more insulation → lower heat loss
- higher wall/insulation thermal conductivity → higher heat loss
- more solar radiation → higher solar gain
- larger openings → greater heat exchange (loss and gain)

It is explicitly **not** claimed to be ANSYS-accurate.

## 8. Optimization abstraction

`app/services/optimization_engine.py` defines `OptimizationEngine` and
`MockOptimizationEngine`, which generates candidate designs across a
discrete insulation/opening search space and scores each with the thermal
engine. The real AI/optimization component can later implement the same
interface and be swapped in via `app/dependencies.py` with no route changes.

## 9. ANSYS abstraction

`app/services/simulation_backend.py` defines `SimulationBackend`,
`MockSimulationBackend` (always available), and `ANSYSSimulationBackend`
(reports itself as unavailable and raises
`SimulationBackendUnavailableError` → HTTP 503 — it never fabricates ANSYS
output).

## 10. Mock mode

Everything in this phase — storage, weather, thermal physics, optimization,
and the ANSYS backend — runs in mock/in-memory mode. No external services,
API keys, or databases are required.

## 11. Configuration

Settings are read from environment variables / a `.env` file via
`app/core/config.py` (Pydantic Settings). See `.env.example`:

```
APP_NAME=Passive Shelter API
APP_VERSION=1.0.0
DEBUG=true
ALLOWED_ORIGINS=http://localhost:5173
```

Copy it to `.env` and adjust as needed. `ALLOWED_ORIGINS` is comma-separated
and feeds CORS configuration.

## 12. Testing

`pytest` covers: health, project CRUD, design validation, climate APIs,
material APIs, simulation create/run/results, optimization create/run,
recommendation (incl. explainability and "no designs" 404), comparison,
JSON + Markdown reports, invalid-ID handling, general error handling, and
CORS preflight — all without PostgreSQL, ANSYS, or external APIs.

## 13. How React will connect later

The frontend will call this API directly over HTTP from
`http://localhost:5173` (already whitelisted in CORS). No route contracts
need to change — the frontend only needs the OpenAPI schema at `/openapi.json`
(or the interactive docs at `/docs`) to generate a typed client.

## 14. How PostgreSQL will replace in-memory storage later

`app/repositories/memory_repository.py` exposes a small, uniform interface
(`add`, `get`, `list`, `delete`, `exists`) per entity type via
`RepositoryRegistry`. A future SQLAlchemy-backed repository implementing the
same interface can be swapped in through `app/dependencies.py` — services and
routes are written against the interface, not the in-memory implementation,
so no other code changes are required.

---

## Installation

```bash
cd phase10_backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Run

```bash
uvicorn app.main:app --reload
```

Then open:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI schema: http://localhost:8000/openapi.json

## Test

```bash
pytest
```

> **Note:** this project was assembled and statically verified (all files
> pass `python -m py_compile`, and every route/schema/service was manually
> cross-checked for consistency) in an environment without internet access,
> so `pip install` and `pytest` could not be executed here. Running the two
> commands above in a normal environment will install dependencies and
> execute the full test suite.

## Example curl requests

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Create a project
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "Ladakh Winter Shelter", "location": "Leh, Ladakh, India", "description": "Cold-climate demo"}'

# List materials (insulation only)
curl "http://localhost:8000/api/v1/materials?category=insulation"

# List climate presets
curl http://localhost:8000/api/v1/climate/presets

# Create a design (replace IDs with real material/project IDs from above)
curl -X POST http://localhost:8000/api/v1/designs \
  -H "Content-Type: application/json" \
  -d '{
    "length": 8, "width": 6, "height": 3,
    "wall_thickness": 0.4, "roof_thickness": 0.2, "floor_thickness": 0.15,
    "insulation_thickness": 0.08, "opening_percentage": 10, "orientation": "S",
    "wall_material": "mat_rammed_earth", "roof_material": "mat_concrete",
    "floor_material": "mat_concrete", "insulation_material": "mat_rammed_earth",
    "occupants": 4, "floor_area": 48, "target_min_temperature": 18, "target_max_temperature": 26,
    "project_id": "proj_xxx"
  }'

# Create + run a simulation
curl -X POST http://localhost:8000/api/v1/simulations \
  -H "Content-Type: application/json" \
  -d '{"project_id": "proj_xxx", "design_id": "design_xxx", "climate_id": "climate_xxx"}'
curl -X POST http://localhost:8000/api/v1/simulations/sim_xxx/run

# Get an explainable recommendation
curl "http://localhost:8000/api/v1/projects/proj_xxx/recommendation?climate_location=Ladakh"

# Full report
curl http://localhost:8000/api/v1/projects/proj_xxx/report
curl http://localhost:8000/api/v1/projects/proj_xxx/report/markdown
```

## Example API response — `GET /api/v1/health`

```json
{
  "status": "ok",
  "service": "passive-shelter-api",
  "version": "1.0.0"
}
```

## Example API response — `POST /api/v1/simulations/{id}/run`

```json
{
  "id": "sim_a1b2c3d4e5f6",
  "project_id": "proj_...",
  "design_id": "design_...",
  "climate_id": "climate_...",
  "duration": 24,
  "timestep": 1,
  "status": "COMPLETED",
  "progress": 1.0,
  "backend": "MOCK",
  "error": null,
  "created_at": "2026-09-13T00:00:00Z",
  "updated_at": "2026-09-13T00:00:05Z"
}
```
