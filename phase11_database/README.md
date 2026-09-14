# Phase 11 — Database + Persistence Layer

Passive Shelter Design Platform — SIH 2026

## 1. Purpose

This phase implements the **persistent storage layer** for the AI-based
passive-shelter design platform: a real PostgreSQL database, a
SQLAlchemy 2.x ORM layer, Alembic migrations, seed data, and a
repository layer for CRUD access.

It is fully self-contained. It does **not** depend on any other phase,
and it does not implement FastAPI routes, the thermal simulation
engine, the optimizer, or ANSYS/weather-API integration — those are
separate phases that will sit on top of this one.

## 2. Architecture

```
FastAPI (Phase 12, not part of this phase)
   ↓
Service layer (Phase 12, not part of this phase)
   ↓
Repository layer   <-- this phase (app/repositories)
   ↓
SQLAlchemy ORM      <-- this phase (app/models)
   ↓
PostgreSQL
```

The repository layer is the only thing a future FastAPI service layer
should import. It knows nothing about HTTP, FastAPI, or Pydantic
request/response schemas — it works entirely in terms of SQLAlchemy
sessions and ORM objects, which keeps it reusable from a web app, a
CLI, a notebook, or a test suite.

## 3. Database Schema

```
Projects
   │
   ├── Designs
   │      └── (wall / roof / floor / insulation) Materials
   │
   ├── Simulations
   │      └── Simulation Results
   │
   ├── Optimization Runs
   │      └── Optimization Candidates
   │
   ├── Recommendations
   │
   └── Reports

Climate Profiles
   └── Climate Data (time series)
```

| Table                     | Purpose                                                            |
|---------------------------|---------------------------------------------------------------------|
| `projects`                | A shelter design project (site, location, climate type)             |
| `materials`                | Reusable material library (WALL / ROOF / FLOOR / INSULATION)        |
| `climate_profiles`         | Named climate contexts (e.g. "Ladakh / High Altitude Cold")         |
| `climate_data`              | Time-series weather observations per climate profile                |
| `designs`                  | A candidate shelter geometry + material selection for a project     |
| `simulations`              | A thermal simulation run against a design + climate profile         |
| `simulation_results`        | Time-series output of a simulation                                  |
| `optimization_runs`         | An optimization run (e.g. NSGA-II) against a project                |
| `optimization_candidates`   | Individual candidate designs evaluated during an optimization run   |
| `recommendations`           | The final recommended design + explanation for a project            |
| `reports`                   | Generated JSON/Markdown reports for a project                       |

All primary keys are PostgreSQL `UUID`s (generated client-side via
`uuid.uuid4()` at insert time), which makes them safe to expose
externally through a future API without leaking sequential IDs.

## 4. Table Relationships

- `Project` → `designs`, `simulations`, `optimization_runs`,
  `recommendations`, `reports` (all cascade-delete with the project).
- `ClimateProfile` → `climate_data` (cascade-delete).
- `Design` → `project`, `wall_material`, `roof_material`,
  `floor_material`, `insulation_material` (each a nullable FK to
  `materials`).
- `Simulation` → `project`, `design`, `climate_profile`, and owns
  `results` (cascade-delete).
- `OptimizationRun` → `project`, `baseline_design`, `best_design`, and
  owns `candidates` (cascade-delete).
- `Recommendation` → `project`, `design`, `optimization_run`.

## 5. Environment Configuration

Copy `.env.example` to `.env` and edit as needed:

```
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/passive_shelter
TEST_DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/passive_shelter_test
SQL_ECHO=false
```

Nothing is hard-coded — `app/core/config.py` reads these via
`pydantic-settings`, and `app/core/database.py` and `alembic/env.py`
both read the resolved URL from there. No password is ever printed or
logged.

## 6. PostgreSQL Setup

**Linux / macOS:**
```bash
createdb passive_shelter
# optional, only needed to run the test suite:
createdb passive_shelter_test
```

**Windows (using the `createdb` tool from a PostgreSQL install, in
Command Prompt or PowerShell):**
```powershell
createdb -U postgres passive_shelter
createdb -U postgres passive_shelter_test
```

If you'd rather use `psql`:
```sql
CREATE DATABASE passive_shelter;
CREATE DATABASE passive_shelter_test;
```

## 7. Install Dependencies

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

pip install -r requirements.txt
```

## 8. Alembic Migrations

An initial migration (`alembic/versions/845dce14a600_initial_schema.py`)
is already included and creates every table, index, foreign key and
constraint described above — you don't have to autogenerate it, just
apply it:

```bash
alembic upgrade head
```

To confirm autogenerate stays in sync with the ORM models after future
model changes:

```bash
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

Roll back the most recent migration:

```bash
alembic downgrade -1
```

## 9. Seed Data

Seed scripts are idempotent — safe to run as many times as you like,
they upsert by unique name and never create duplicates.

```bash
python -m app.seed.seed_materials
python -m app.seed.seed_climate
```

`seed_materials.py` loads a realistic material library: concrete,
fired clay brick, local stone, timber, an insulated sandwich panel,
mineral wool, EPS, XPS, rammed earth, and a concrete floor slab, each
with representative (not certified) thermal properties.

`seed_climate.py` loads four named climate profiles — **Ladakh / High
Altitude Cold**, **Hot & Dry**, **Warm & Humid**, and **Composite** —
and a deterministic 24-hour sample `climate_data` series for the
Ladakh profile (illustrative values, not live weather-API data).

## 10. Repository Architecture

Every table has a corresponding repository under `app/repositories/`,
all built on a small generic `BaseRepository` (`create`, `get`,
`get_or_404`, `list`, `update`, `delete`) plus domain-specific query
methods:

- `ProjectRepository` — `get_by_name`, `list_by_location`
- `MaterialRepository` — `get_by_name`, `list_by_category`, `list_active`
- `ClimateRepository` — profile CRUD + `add_climate_data_point`,
  `bulk_add_climate_data`, `get_climate_data`
- `DesignRepository` — `list_by_project`, `get_baseline`
- `SimulationRepository` — `list_by_project`, `list_by_design`,
  `add_result`, `bulk_add_results`, `get_results`
- `OptimizationRepository` — `list_by_project`, `add_candidate`,
  `list_candidates`
- `RecommendationRepository` — `list_by_project`
- `ReportRepository` — `list_by_project`

Repositories never call `commit()`/`rollback()` themselves beyond an
internal `flush()` to get generated values back — the transaction
boundary belongs to the caller. Use the `get_session()` context
manager from `app/core/database.py`, which commits on success and
rolls back (and always closes the session) on any exception:

```python
from app.core.database import get_session
from app.repositories.project_repository import ProjectRepository

with get_session() as session:
    repo = ProjectRepository(session)
    project = repo.create(name="Leh Field Shelter", location="Leh, Ladakh")
    print(project.id)
# committed and session closed automatically here
```

## 11. Running Tests

The suite uses a real PostgreSQL test database (`TEST_DATABASE_URL`,
or `DATABASE_URL` with `_test` appended as a fallback). If that
database isn't reachable, the whole session is skipped with a clear
message rather than silently mocking the database — production
configuration stays strictly PostgreSQL either way.

```bash
pytest
```

16 tests cover: database connection, Project/Material/Climate/Design/
Simulation/Optimization/Recommendation/Report CRUD, climate and
simulation time-series bulk insertion, material relationships on a
design, foreign-key relationships, check constraints, and rollback/
error handling.

## 12. How the Phase 12 FastAPI Backend Will Connect

Phase 12 will add a thin service layer that:

1. Opens a session per request (e.g. as a FastAPI dependency wrapping
   `get_session()`).
2. Instantiates the relevant repository/repositories from this phase.
3. Converts ORM objects to Pydantic response schemas.

No FastAPI-specific logic lives inside `app/repositories/` — routes
and request/response models belong entirely to Phase 12, so this
layer can be reused unchanged.

## 13. How Simulation and Optimization Results Will Be Stored

- A simulation run is created as a `simulations` row (`status=CREATED`,
  `backend=MOCK` or `ANSYS`). As it progresses, its `status`,
  `started_at`/`completed_at`, and aggregate summary columns
  (`average_temperature`, `comfort_percentage`,
  `external_energy_requirement`, etc.) are updated in place, while its
  time-series output is streamed into `simulation_results` via
  `SimulationRepository.bulk_add_results` — indexed on
  `(simulation_id, timestamp)` for fast range queries even with
  thousands of rows per run.
- An optimization run is created as an `optimization_runs` row; each
  design it evaluates is written once to `designs` and once to
  `optimization_candidates` (score breakdown + rank), linked back to
  the run via `optimization_run_id`.
- The final choice is written to `recommendations`, linking the
  winning `design_id` and the `optimization_run_id` that produced it,
  with `trade_offs`/`assumptions`/`limitations` stored as JSONB for
  flexible, structured explanation data.

## 14. Scaling Considerations

- `climate_data` and `simulation_results` are the two tables expected
  to grow into the thousands-to-millions of rows; both are indexed on
  `(parent_id, timestamp)` to keep range queries fast, and both use
  bulk-insert repository methods (`bulk_add_climate_data`,
  `bulk_add_results`) rather than row-by-row inserts.
- Every foreign key that's commonly filtered on
  (`designs.project_id`, `simulations.project_id`,
  `simulations.design_id`, `optimization_runs.project_id`,
  `optimization_candidates.optimization_run_id`) has its own index.
- `projects.location` is indexed for location-based lookups.
- No unnecessary indexes are added — write-heavy time-series tables
  only carry the one composite index they need.
- UUID primary keys mean sharding or merging databases later doesn't
  require renumbering any IDs.

## 15. Complete File Tree

```
phase11_database/
├── app/
│   ├── __init__.py
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── mixins.py
│   │   ├── project.py
│   │   ├── design.py
│   │   ├── material.py
│   │   ├── climate.py
│   │   ├── simulation.py
│   │   ├── simulation_result.py
│   │   ├── optimization.py
│   │   ├── optimization_candidate.py
│   │   ├── recommendation.py
│   │   └── report.py
│   ├── repositories/
│   │   ├── base_repository.py
│   │   ├── project_repository.py
│   │   ├── design_repository.py
│   │   ├── material_repository.py
│   │   ├── climate_repository.py
│   │   ├── simulation_repository.py
│   │   ├── optimization_repository.py
│   │   ├── recommendation_repository.py
│   │   └── report_repository.py
│   └── seed/
│       ├── seed_materials.py
│       └── seed_climate.py
├── alembic/
│   ├── versions/
│   │   └── 845dce14a600_initial_schema.py
│   ├── env.py
│   └── script.py.mako
├── tests/
│   ├── conftest.py
│   ├── test_database.py
│   ├── test_projects.py
│   ├── test_materials.py
│   ├── test_climate.py
│   ├── test_designs.py
│   ├── test_simulations.py
│   ├── test_optimization.py
│   ├── test_recommendations_reports.py
│   └── test_relationships_and_constraints.py
├── alembic.ini
├── pytest.ini
├── requirements.txt
├── .env.example
└── README.md
```

## 16. Quickstart (all commands in order)

```bash
# 1. install deps
pip install -r requirements.txt

# 2. configure
cp .env.example .env      # edit if your Postgres credentials differ

# 3. create databases
createdb passive_shelter
createdb passive_shelter_test   # only needed for pytest

# 4. migrate
alembic upgrade head

# 5. seed
python -m app.seed.seed_materials
python -m app.seed.seed_climate

# 6. test
pytest
```
