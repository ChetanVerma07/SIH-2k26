# Phase 7 — AI-Based Passive Shelter Design: Orchestration & Decision Layer

This is **Phase 7 only** of the SIH 2026 project *"AI-Based Software Model
for Designing Energy-Efficient Passive Shelters for Different Climatic
Conditions."* It is a completely standalone Python project — it does not
import from, or require, any other phase, ANSYS, a database, a frontend,
or external weather APIs.

Phase 7 builds the **orchestration and decision layer** that coordinates
climate data, thermal simulation, design optimization, and engineering
recommendations behind a stable set of interfaces, so real implementations
can later be swapped in without touching the orchestration code.

---

## ⚠️ Engineering Transparency — read this first

This project currently ships **only mock components**. Please keep these
categories distinct:

| Category | Status in this repo |
|---|---|
| **REAL ENGINEERING SIMULATION** | ❌ Not present. No EnergyPlus/CFD/FEA solver is used. |
| **MOCK SIMULATION** | ✅ `MockClimateProvider`, `MockThermalSimulator`, `MockDesignOptimizer` implement a simplified, transparent, deterministic heat-balance model (see `app/mocks/thermal.py` docstring) for orchestration development and testing only. |
| **FUTURE ANSYS VALIDATION** | 🔲 `ANSYSValidator` interface + `MockANSYSValidator` are provided so a real ANSYS scripting/batch integration can be dropped in later without changing the orchestrator. All mock ANSYS results are explicitly labeled `is_mock=True` and must never be treated as real validation. |
| **FUTURE AI/ML COMPONENTS** | 🔲 `DesignOptimizer` currently uses a fixed deterministic grid search (`MockDesignOptimizer`). A genetic algorithm, Bayesian optimizer, or generative ML model can replace it behind the same interface. |

**Final engineering deployment of any recommended design requires, at minimum:**
- Validated material properties (measured, not assumed, thermal conductivities)
- Calibrated, location-specific climate inputs (real station/satellite data)
- ANSYS or other high-fidelity FEA/CFD simulation
- Experimental validation where appropriate
- Domain-expert (structural/thermal engineer) review

Do not use any output of this repository for real construction decisions.

---

## Architecture

```
User Request
     │
     ▼
ClimateProvider  ──▶  DesignOptimizer  ──▶  ThermalSimulator  ──▶  ANSYSValidator
     │                                            │                     │
     └────────────────────────┬───────────────────┴─────────────────────┘
                               ▼
                     Orchestrator (services/orchestrator.py)
                               │
              ┌────────────────┼─────────────────┐
              ▼                ▼                  ▼
        RobustnessSvc   ConfidenceSvc     RecommendationSvc
              │                │                  │
              └────────────────┴──────────────────┘
                               ▼
                       EngineeringReport
                     (JSON + Markdown export)
```

The `Orchestrator` class (`app/services/orchestrator.py`) depends **only**
on the four abstract interfaces in `app/interfaces/`, injected through its
constructor:

```python
Orchestrator(
    climate_provider=MockClimateProvider(),
    thermal_simulator=MockThermalSimulator(),
    optimizer=MockDesignOptimizer(),
    ansys_validator=MockANSYSValidator(),
)
```

It never imports or instantiates a concrete mock class internally. To plug
in real components later:

1. Write a new class implementing `ClimateProvider` (e.g. wrapping a real
   weather API) — it must return a `ClimateProfile` and a list of
   `ScenarioDefinition`.
2. Write a new class implementing `ThermalSimulator` (e.g. wrapping
   EnergyPlus) — it must return a `ThermalPerformance` for a given design.
3. Write a new class implementing `DesignOptimizer` (e.g. a GA/ML search)
   — it must return candidate `ShelterDesign` objects and a baseline.
4. Write a new class implementing `ANSYSValidator` — it must submit a job
   and return an `ANSYSValidationResult` with `is_mock=False`.
5. Swap the four lines in `app/main.py` (or wherever you construct the
   `Orchestrator`) to point at the new classes. No orchestration, service,
   or API code changes.

## Project structure

```
phase7_orchestration/
├── app/
│   ├── main.py                    FastAPI service + endpoint wiring
│   ├── models/                    Pydantic data models
│   │   ├── request.py             ShelterDesignRequest, WhatIfRequest, CompareRequest
│   │   ├── design.py               ShelterDesign + material property tables
│   │   ├── climate.py              ClimateProfile, ScenarioDefinition
│   │   ├── results.py              ThermalPerformance, RobustnessSummary, etc.
│   │   └── report.py               EngineeringReport (+ to_markdown())
│   ├── interfaces/                 Abstract base classes (the "contracts")
│   │   ├── climate.py  thermal.py  optimizer.py  ansys.py
│   ├── mocks/                      Deterministic mock implementations
│   │   ├── climate.py  thermal.py  optimizer.py  ansys.py
│   ├── services/                   Orchestration + decision logic
│   │   ├── orchestrator.py         run_design_analysis() — the main workflow
│   │   ├── recommendation.py       Explains the selected design from real metrics
│   │   ├── robustness.py           Multi-scenario evaluation
│   │   ├── what_if.py              Single-parameter sensitivity analysis
│   │   └── confidence.py           Transparent, formula-based confidence scoring
│   └── reporting/
│       └── report_generator.py     JSON + Markdown export helpers
├── examples/
│   └── ladakh_demo.py              End-to-end runnable demo
├── tests/                          pytest suite (13 categories, see below)
├── requirements.txt
├── pytest.ini
└── README.md
```

## How the mock thermal model works (transparency)

`app/mocks/thermal.py` implements a simplified single-zone conductance
(UA) heat-balance model, run hour-by-hour over the simulation duration:

- **Envelope conductance (UA)** is built from wall material conductivity
  + insulation thickness (series thermal resistance), an assumed
  double-glazed opening U-value, and per-material roof/floor U-values.
- **Heat loss / heating requirement** are computed against a fixed
  setpoint (the comfort-range midpoint) — a standard degree-day-style
  approach — so they respond monotonically and transparently to
  insulation and material choice.
- **Solar gain** is a function of opening area, a fixed solar heat gain
  coefficient, orientation (south-facing = maximum, per a cosine model),
  and a daylight-hours bell curve.
- **Passive indoor temperature** (used only for comfort%/min/max/avg
  reporting) combines outdoor temperature with a solar-driven offset,
  smoothed by an insulation-dependent factor as a simple thermal-mass
  proxy.

All constants are documented in code comments and are **illustrative
approximations**, not measured or certified engineering data.

## Installation

```bash
cd phase7_orchestration
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running the API

```bash
uvicorn app.main:app --reload
```

Then open `http://127.0.0.1:8000/docs` for interactive Swagger UI.

## Running tests

```bash
pytest
```

Tests run entirely offline against the mock components — no ANSYS,
database, or internet access is required. The suite covers:

1. Request validation (`test_request_validation.py`)
2. Climate provider interface (`test_climate_provider.py`)
3. Thermal simulator interface (`test_thermal_simulator.py`)
4. Optimizer interface (`test_optimizer.py`)
5. ANSYS validator interface (`test_ansys_validator.py`)
6. Complete orchestration workflow (`test_orchestration.py`)
7. Baseline comparison (`test_orchestration.py`)
8. Scenario robustness (`test_robustness.py`)
9. What-if analysis (`test_what_if.py`)
10. Confidence calculation (`test_confidence.py`)
11. Recommendation generation (`test_recommendation.py`)
12. Report generation (`test_report_generation.py`)
13. API endpoints (`test_api.py`)

## Running the Ladakh demo

```bash
python examples/ladakh_demo.py
```

This prints a concise engineering summary to the console and writes
`examples/output/ladakh_report.json` and `ladakh_report.md`.

## Example API requests

### `GET /api/health`
```bash
curl http://127.0.0.1:8000/api/health
```
```json
{"status": "ok", "mock_mode": true, "version": "7.0.0"}
```

### `POST /api/analyze`
```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Ladakh",
    "climate_description": "cold high-altitude",
    "comfort_range": {"min_c": 18, "max_c": 26},
    "objectives": ["maximize thermal comfort", "minimize heat loss", "minimize external energy requirement"],
    "simulation_duration_hours": 24
  }'
```

Response shape:
```json
{
  "project": {"...": "..."},
  "location": "Ladakh",
  "climate": {"...": "..."},
  "design_input": {"...": "..."},
  "simulation": {"...": "..."},
  "recommended_design": {"...": "..."},
  "baseline_design": {"...": "..."},
  "results": {"...": "..."},
  "baseline_results": {"...": "..."},
  "comparison": {"...": "..."},
  "robustness": {"scenarios": ["..."], "robustness_score": 74.2},
  "ansys_validation": {"is_mock": true, "...": "..."},
  "confidence": {"data_confidence": 90.0, "simulation_confidence": 89.0, "recommendation_confidence": 84.5},
  "recommendation": {"headline": "...", "reasons": ["..."], "tradeoffs": ["..."]},
  "assumptions": ["..."],
  "limitations": ["..."]
}
```

### `POST /api/what-if`
```bash
curl -X POST http://127.0.0.1:8000/api/what-if \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Ladakh",
    "climate_description": "cold high-altitude",
    "comfort_range": {"min_c": 18, "max_c": 26},
    "parameter": "insulation_thickness_m",
    "new_value": 0.3
  }'
```

### `POST /api/compare`
```bash
curl -X POST http://127.0.0.1:8000/api/compare \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Ladakh",
    "climate_description": "cold high-altitude",
    "comfort_range": {"min_c": 18, "max_c": 26},
    "design_ids": ["baseline", "candidate-01"]
  }'
```

### `GET /api/demo`
```bash
curl http://127.0.0.1:8000/api/demo
```
Runs the full Ladakh workflow and returns the same `EngineeringReport`
shape as `/api/analyze`.

## Notes on this being Phase 7 only

- No previous phase folders are required or imported.
- No ANSYS installation is required (mock adapter only).
- No frontend is required (JSON API only; Swagger UI is provided free by FastAPI).
- No database is required (all state is computed per-request).
- No external weather API is required (deterministic mock climate provider).
