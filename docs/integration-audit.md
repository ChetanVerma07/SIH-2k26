# Phase 12 Integration Audit

## Canonical Components

| Phase | Purpose | Entry point | Language/framework | Runtime dependencies | Inputs/outputs | Status |
|---|---|---|---|---|---|---|
| 1 | Deterministic thermal physics engine and material calculations | `phase1_thermal_engine/main.py` | Python | Python standard library and pytest | Shelter/material/climate values -> thermal metrics | Preserved; backend currently uses its own compatible mock engine interface |
| 2 | Earlier frontend prototype | `phase2/src/main.tsx` | React/TypeScript/Vite | npm packages | UI state -> browser UI | Superseded by canonical `frontend/` |
| 3 | Earlier FastAPI API prototype | `phase3_thermal_api/app/main.py` | Python/FastAPI | FastAPI and pytest | API payloads -> thermal responses | Superseded by canonical `backend/` |
| 4 | ANSYS thermal experiment | `phase4_ansys_thermal/` | Python | Python and optional ANSYS environment | Thermal input -> generated/ANSYS-oriented outputs | Preserved as experiment; not executed by default |
| 5 | Weather/climate module | `phase5_weather_module/` | Python | Python HTTP/data tooling | Weather inputs -> climate records | Preserved as source material; canonical backend uses bundled climate presets |
| 6 | Optimization experiments | `phase6/` | Python | Python numerical tooling | Design candidates -> scores | Preserved; canonical backend uses `MockOptimizationEngine` interface |
| 7 | Orchestration experiment | `phase7_orchestration/` | Python | Python | Pipeline inputs -> orchestration results | Preserved; canonical service layer owns current API workflow |
| 8 | ANSYS bridge/pipeline | `phase8_ansys_bridge/` | Python | Python and optional ANSYS | Prepared files/process output -> parsed results | Preserved; unavailable status is explicit when not configured |
| 9 | React dashboard UI | `phase9_frontend/` | React/TypeScript/Vite/Vitest | npm packages | User forms -> dashboard pages | Source for canonical `frontend/`; mocks retained as fallback |
| 10 | REST API/service layer | `phase10_backend/` | Python/FastAPI/Pydantic | FastAPI, pytest, httpx | REST resources -> validated service responses | Source for canonical `backend/`; 47 tests pass |
| 11 | SQLAlchemy/Alembic database layer | `phase11_database/` | Python/SQLAlchemy/Alembic/PostgreSQL | psycopg, SQLAlchemy, Alembic | Domain records -> PostgreSQL tables | Retained under `database/`; not active in current in-memory API runtime |
| 12 | Final integration | root `backend/`, `frontend/`, `database/`, `data/`, `docs/` | FastAPI + React | Python + npm | Frontend -> FastAPI -> services/repositories | Active canonical structure |

## Canonical Runtime

- Backend: `backend/app/main.py`
- Frontend: `frontend/src/main.tsx`
- Database migration package: `database/alembic/`
- Bundled data: `backend/data/` and `data/`
- Environment template: `.env.example`

## Compatibility Matrix

| Component | Input | Output | Integration method | Status |
|---|---|---|---|---|
| Climate and weather | Location/preset selection | Frontend `ClimateData` | `frontend/src/api/climateApi.ts` adapts `/climate/presets` and `/climate/current/{location}`; backend `WeatherService` owns the optional provider call | Live with labelled preset fallback |
| Materials | Category/material ID | Frontend `Material` | `frontend/src/api/materialsApi.ts` adapts snake_case fields and categories | Live with deterministic fallback |
| Project creation | Analysis form | `ProjectResponse` + frontend `AnalysisProject` | `analysisApi.createAnalysis()` posts `/projects` | Live in non-test mode |
| Design creation | Frontend design and requirements | `DesignResponse` | `analysisApi.createAnalysis()` converts camelCase, orientation, and material IDs | Live in non-test mode |
| Thermal simulation | Project/design/climate IDs | Simulation status/results | `simulationApi.runSimulation()` creates and runs `/simulations` | Live in non-test mode |
| Optimization | Project/baseline design/parameters | Candidate scores | Existing backend mock optimizer and routes | Backend available; frontend result adapter remains follow-up |
| Recommendation | Project and climate | Recommendation explanation | Existing backend recommendation route | Backend available; frontend result adapter remains follow-up |
| Reports | Project and climate | JSON/Markdown report | Existing backend report routes | Backend available; frontend report remains mock-shaped |
| PostgreSQL | SQLAlchemy models/migrations | Persistent records | `database/` package and Alembic | Migration path; not wired into canonical API runtime |
| ANSYS | Configured executable and working directory | Parsed thermal results | Existing unavailable backend abstraction | Explicitly not configured by default |

## Environment Variables

Required for the validated local mock/in-memory runtime:

- `ALLOWED_ORIGINS`
- `VITE_API_BASE_URL`
- `VITE_USE_MOCK_API` (optional)

Reserved for optional integrations:

- `DATABASE_URL`
- `TEST_DATABASE_URL`
- `WEATHER_API_KEY`
- `WEATHER_API_BASE_URL`
- `ANSYS_EXECUTABLE_PATH`
- `ANSYS_WORKING_DIRECTORY`

The optional current-weather provider uses `WEATHER_API_KEY` and
`WEATHER_API_BASE_URL` only on the backend. React never receives or sends the
provider credential.

No real secrets are committed.

## Verified Commands

```powershell
cd backend
py -3.10 -m pytest -q

cd ..\frontend
npm run test
npm run build
```

The live Ladakh workflow was also verified through the backend: project creation,
design creation, climate lookup, simulation creation, simulation execution, and
result retrieval returned `COMPLETED` with thermal metrics.

## Known Limitations

1. The canonical API currently uses in-memory repositories. The Phase 11
   PostgreSQL layer is not yet injected into `backend/app/dependencies.py`.
2. The backend thermal and optimization implementations are deterministic mock
   engines, not ANSYS/CFD or production AI output.
3. The frontend optimization, comparison, recommendation, and report pages
   still use the original richer mock view models; their backend contracts need
   additional response adapters.
4. Docker was unavailable during verification, so manual startup is the
   supported and tested procedure.
