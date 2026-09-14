# Phase 4 — ANSYS Thermal Simulation Workflow & Automation Layer

Part of the SIH 2026 project **"AI-Based Software Model for Designing
Energy-Efficient Passive Shelters for Different Climatic Conditions"**.

This is a **completely independent, standalone component**. It does not
require a frontend, a database, cloud deployment, or code from any
other phase. It runs entirely on a normal computer with Python 3.9+,
with no ANSYS installation required to see it work end-to-end.

---

## 1. Purpose

Phase 4 provides the thermal-simulation workflow and automation layer
that later phases (frontend, weather-data system, optimization engine,
ML model) will call into. Given shelter geometry, materials, and
climate/boundary conditions, it prepares a thermal simulation, runs it
(or prepares it for ANSYS), and returns normalized engineering results:
temperature distribution, heat flux, total heat flow, surface-by-surface
heat loss, solar gain, and time-series indoor temperature.

## 2. ANSYS's role

ANSYS availability, licensing, and installed products differ between
development machines, CI systems, and production deployments. This
package therefore treats ANSYS as a **pluggable backend**, not a hard
dependency:

- On a machine **without** ANSYS: the package generates ANSYS-ready
  input files (JSON config + APDL skeleton) and runs a **mock**
  simplified Python thermal model so the whole pipeline is exercisable
  end-to-end.
- On a machine **with** a licensed ANSYS installation and PyMAPDL: the
  same architecture has a real integration point (`AnsysThermalAdapter`)
  ready to be completed/extended for that environment (see §12).

**No part of this package invents or fakes ANSYS results.** Mock
results are always explicitly labelled `MOCK SIMULATION — NOT ANSYS
RESULT` in the returned data and cannot be produced with `is_mock=False`.

## 3. Architecture

```
phase4_ansys_thermal/
├── ansys_thermal/
│   ├── __init__.py
│   ├── models/
│   │   ├── geometry.py        # ShelterGeometry (rectangular shelter params)
│   │   ├── materials.py       # Material, MaterialAssignment, example library
│   │   ├── climate.py         # HourlyClimatePoint, BoundaryConditions, builders
│   │   └── simulation.py      # SimulationConfig (bundles the above)
│   ├── geometry/
│   │   └── shelter_builder.py # geometry -> ANSYS-ready element list
│   ├── ansys/
│   │   ├── adapter.py         # ThermalSimulationAdapter, Mock + Ansys adapters
│   │   ├── input_generator.py # JSON config, human summary, APDL skeleton
│   │   ├── executor.py        # lumped-parameter thermal engine (mock only)
│   │   └── result_parser.py   # documented JSON/CSV result parsing
│   ├── results/
│   │   └── normalizer.py      # raw results -> common normalized schema
│   ├── validation/
│   │   └── validators.py      # physical-plausibility checks
│   ├── comparison.py           # multi-design batch runner + metrics table
│   └── visualization.py        # matplotlib plotting utilities
├── examples/
│   └── ladakh_demo.py          # full end-to-end mock demonstration
├── tests/                       # pytest suite, runs without ANSYS
├── generated/                   # output directory for generated artifacts
├── requirements.txt
└── README.md
```

Design principle: **A (prep) / B (ANSYS execution adapter) / C (result
extraction) / D (normalization)** are cleanly separated. Nothing in
`models/`, `geometry/`, or `validation/` imports from `ansys/`, so the
data model can be reused by a real ANSYS path, the mock path, or a
future different solver without change.

## 4. Geometry

`ShelterGeometry` (in `models/geometry.py`) supports a **rectangular**
shelter (per the Phase 4 base requirement) parameterized by: length,
width, height, wall/roof/floor thickness, window/door/other-opening
areas, and orientation (degrees from North). A `shape` field
(`ShelterShape` enum) exists so future phases can add new shapes
(dome, vault, L-shaped, ...) without changing the surrounding
architecture — only `shelter_builder.py` would need a new builder
function for each new shape.

`shelter_builder.build_rectangular_shelter()` translates geometry into
a list of `ShelterElement`s (walls, roof, floor, openings) with area,
thickness, orientation, and exposure flags — the form the ANSYS input
generator and the mock solver both consume.

## 5. Materials

`Material` (in `models/materials.py`) captures thermal conductivity,
density, specific heat, emissivity, and solar absorptivity. Eight
example materials are bundled (`EXAMPLE_MATERIALS`): rammed earth,
burnt clay brick, dense concrete, AAC block, EPS insulation, single &
double glass, and softwood timber, with commonly-cited approximate
engineering property values. **These are convenient starting points,
not a substitute for manufacturer datasheets or material testing** —
say so explicitly if you use them in a real design.

Materials are fully independent of the ANSYS execution layer; a
`MaterialAssignment` maps one `Material` to each of wall/roof/floor/
window.

## 6. Boundary conditions

`BoundaryConditions` (in `models/climate.py`) holds: an ambient climate
time series (`HourlyClimatePoint` — hour, ambient temperature, solar
irradiance, optional wind speed), indoor initial temperature, internal
and external convection coefficients, ground temperature, time step,
and duration.

**Documented defaults** (used only if not overridden):

| Field | Default | Basis |
|---|---|---|
| `indoor_initial_temp_c` | 20.0 °C | assumed comfortable start point, not a measurement |
| `internal_convection_w_m2k` | 8.0 W/m²K | typical indoor natural convection (engineering default) |
| `external_convection_w_m2k` | 23.0 W/m²K | typical external convection, moderate wind (engineering default) |
| `ground_temp_c` | 10.0 °C | generic deep-ground default — replace with site data |
| `time_step_s` | 3600 s | 1 hour |
| `duration_hours` | 24 | one day |

Nothing silently invents a measured ambient temperature or solar
value — the `ambient_series` must be supplied explicitly (helper
builders `build_constant_climate()` and `build_diurnal_climate()` are
provided for tests/demos, and are documented as simplified/synthetic,
not real weather data).

## 7. Simulation workflow

```
INPUT
  -> ShelterGeometry, MaterialAssignment, BoundaryConditions (models/)
  -> SimulationConfig bundles them
  -> validate_simulation_config() checks physical plausibility
  -> shelter_builder.build_rectangular_shelter() creates the element list
  -> ThermalSimulationAdapter.run_full_workflow():
       prepare_model() -> apply_materials() -> apply_boundary_conditions()
       -> configure_analysis() -> execute() -> extract_results()
  -> normalizer.normalize_result() produces the common result schema
  -> (optional) visualization.py plots; comparison.py for multi-design runs
```

Target analysis type: **transient thermal**. The mock engine
conceptually accounts for conduction (wall/roof/floor/opening),
convection (internal + external films), solar heat input (direct
through openings + sol-air effect on opaque surfaces), thermal mass
(indoor air + an effective wall mass layer), and ground coupling
through the floor. **This is a simplified lumped-parameter
approximation for demonstration — not a substitute for an ANSYS finite
element solve**, which is required for a validated design.

## 8. ANSYS integration strategy

Two adapters implement `ThermalSimulationAdapter`:

- **`MockThermalAdapter`** — runs `ansys/executor.py`'s lumped thermal
  network model. No ANSYS or PyMAPDL required. Always returns
  `is_mock=True` results with an explicit warning.

- **`AnsysThermalAdapter`** — the real integration point:
  1. `prepare_model()` always generates the ANSYS-ready artifacts
     (JSON config, human summary, APDL `.dat` skeleton) via
     `input_generator.py`, regardless of whether live execution will
     succeed.
  2. `execute()` attempts to `import ansys.mapdl.core` (PyMAPDL) and
     launch a live MAPDL session. If PyMAPDL isn't installed, or no
     licensed ANSYS installation/instance can be reached, it raises
     `AnsysNotAvailableError` with a clear message pointing to the
     generated fallback artifacts. It does **not** silently fall back
     to the mock model.
  3. If a live MAPDL session *is* reached, the adapter currently still
     raises `AnsysNotAvailableError` at the "run the generated model"
     step, because meshing review, boundary-condition application via
     `SF`/`SFE`, and time-varying tabular solar/ambient loads need to
     be finalized and validated against the **specific ANSYS
     version and license** in the target deployment — this is
     explicitly a next-step integration task, not something this
     package can honestly claim to have validated without a real
     ANSYS environment.
  4. Once an engineer has run the generated `.dat` skeleton (or their
     own refined model) in ANSYS and exported results to the
     documented JSON/CSV format, `extract_results_from_export()`
     parses and normalizes those **real** results (`is_mock=False`).

## 9. Mock simulation mode

`MockThermalAdapter` implements a lumped-parameter thermal network:

- Each element type (wall, roof, floor, opening) contributes a
  conductance `U*A` (external film + conduction + internal film in
  series; floor uses conduction + internal film against
  `ground_temp_c`).
- Indoor air + an effective wall-mass layer (documented assumption:
  0.05 m effective coupled thickness) form the thermal capacitance.
- Solar gain = direct transmission through openings (using
  `1 - window_solar_absorptivity` as a simplified glazing
  transmittance proxy) + a sol-air-temperature-style boost to
  conduction through opaque surfaces.
- Explicit Euler time-stepping updates the indoor temperature each
  step.

This is intentionally simple and clearly documented as an
approximation — it exists to make the full architecture (validation →
input generation → execution → normalization → visualization →
comparison) runnable and testable without ANSYS, **not** to produce
certified thermal performance numbers.

## 10. Result format

All adapters return the same normalized schema
(`results/normalizer.py`):

```json
{
  "meta": {"source": "mock|ansys", "name": "...", "is_mock": true, "warning": "..."},
  "summary": {
    "min_temp_c": 0.0, "max_temp_c": 0.0, "avg_temp_c": 0.0,
    "total_heat_transfer_wh": 0.0, "total_solar_gain_wh": 0.0,
    "simulation_duration_hours": 0.0
  },
  "time_series": [
    {"timestamp_hour": 0.0, "indoor_temp_c": 0.0, "ambient_temp_c": 0.0,
     "heat_flow_w": 0.0, "solar_gain_w": 0.0}
  ],
  "surface_results": {
    "wall_heat_transfer_wh": 0.0, "roof_heat_transfer_wh": 0.0,
    "floor_heat_transfer_wh": 0.0, "opening_heat_transfer_wh": 0.0
  },
  "spatial_results": {
    "min_temp_c": null, "max_temp_c": null, "avg_temp_c": null,
    "heat_flux_stats": null, "note": "..."
  }
}
```

`spatial_results` fields are `null` for the mock adapter (single
lumped indoor node — no spatial resolution). A real ANSYS FE solve
would populate these; the schema already has the slots reserved.

## 11. How to run the mock demonstration

```bash
cd phase4_ansys_thermal
pip install -r requirements.txt
python examples/ladakh_demo.py
```

This builds a cold, high-altitude (Ladakh-like) shelter scenario,
validates it, generates ANSYS input artifacts into
`generated/ladakh_demo/`, runs the mock adapter, prints an engineering
summary, generates 3 plots, and compares 3 orientation/material design
variants. All console output and file names clearly flag mock results.

## 12. How to connect an actual ANSYS installation

1. Install PyMAPDL: `pip install ansys-mapdl-core` and ensure a
   licensed ANSYS Mechanical APDL installation is reachable (local or
   remote) per PyMAPDL's setup docs.
2. Use `AnsysThermalAdapter(config, generated_dir=...)` instead of
   `MockThermalAdapter`. Call `prepare_model()` to get the generated
   `.dat` skeleton, review/refine it in ANSYS Mechanical APDL
   (meshing density, exact BC surface selections, solar tabular
   loads — see §13), then either:
   - Extend `AnsysThermalAdapter.execute()` for your specific ANSYS
     version to script the reviewed model end-to-end via PyMAPDL, or
   - Run the model manually/in batch in ANSYS, export results to the
     documented JSON/CSV schema (see `ansys/result_parser.py`), and
     call `adapter.extract_results_from_export(result_file)`.

## 13. What requires manual ANSYS setup

- **Meshing density and quality** — the generated skeleton sets a
  default `ESIZE,0.1`; production runs should review this per
  geometry/analysis needs.
- **Exact boundary-condition surface selections** — the skeleton
  documents *which* physical BCs apply (external convection with
  time-varying ambient, ground coupling on the floor, solar flux on
  exterior faces) but leaves the ANSYS face/area selection logic
  (`SF`/`SFE` target selection) for the engineer, since it depends on
  the final meshed geometry and any Boolean operations used to build
  the shell.
- **Solar load application method** — applying a time-varying solar
  heat flux as a tabular load (`*DIM` + `SFE` with a table reference)
  needs to be wired to the ANSYS version in use.
- **Any non-rectangular geometry** — only rectangular shelters are
  implemented in Phase 4.
- **Model validation** — comparing ANSYS results against hand
  calculations / known benchmarks before trusting design decisions.

## 14. Assumptions

- Rectangular shelter shape only (Phase 4 scope).
- Openings are modelled as being on walls only (not roof).
- Floor is on-grade, exchanging heat with a fixed ground temperature
  (no separate soil model).
- The mock thermal model uses a single lumped indoor-air node plus an
  effective wall-mass layer — not a spatially resolved model.
- Default convection coefficients, ground temperature, and indoor
  initial temperature are documented generic engineering defaults,
  not site measurements (see §6 table).
- The Ladakh demo's climate series is a documented synthetic sinusoidal
  approximation, not measured meteorological data.

## 15. Limitations

- **The mock adapter is not ANSYS.** It cannot report true spatial
  temperature/heat-flux distribution, cannot resolve multi-dimensional
  conduction effects, and uses simplified solar-gain approximations.
  Results are for demonstrating the pipeline only.
- **`AnsysThermalAdapter`'s live-execution path is not yet complete**
  for any specific ANSYS version/license — see §8, point 3. It has
  been designed with the correct integration points (PyMAPDL import,
  graceful failure, generated fallback artifacts) but scripting the
  full meshing/BC/solve sequence against a live session requires
  validation in an actual licensed environment, which was outside the
  scope/resources of this development environment.
- Only rectangular geometry is supported.
- No radiation heat transfer between interior surfaces is modelled in
  the mock engine (only convection + conduction + solar).
- The design-comparison utility (`comparison.py`) is a batch runner,
  not the AI/optimization engine referenced in the overall SIH
  project — that belongs to a later phase.

## 16. Validation requirements

`validation/validators.py` enforces, before any adapter runs:

- Geometry: positive dimensions, wall thickness not exceeding half the
  smaller plan dimension, non-negative opening areas not exceeding
  gross wall area, orientation in `[0, 360)`, and sanity bounds on
  overall size (catches obvious unit-entry mistakes).
- Materials: positive conductivity/density/specific heat, emissivity
  and solar absorptivity in `[0, 1]`.
- Boundary conditions: at least 2 climate points, positive time step
  and duration, a sanity cap on total time steps (avoids runaway
  simulations), positive convection coefficients, and physically
  plausible temperature/irradiance ranges.

All validators raise `ValidationError` (a `ValueError` subclass) with
a specific, actionable message — nothing is silently clamped or
substituted.

---

## Installation

```bash
cd phase4_ansys_thermal
pip install -r requirements.txt
```

## Running the mock demonstration

```bash
python examples/ladakh_demo.py
```

## Running tests

```bash
pytest
```

All tests run without any ANSYS installation.

## Example configuration

See `examples/ladakh_demo.py::build_ladakh_config()` for a full
example (6 m × 4 m × 2.8 m shelter, rammed-earth walls, dense-concrete
roof/floor, double glazing, cold high-altitude climate profile).
Running the demo also writes the equivalent JSON configuration to
`generated/ladakh_demo/ladakh_passive_shelter_config.json`.

## Example output

Running `python examples/ladakh_demo.py` prints an engineering summary
similar to:

```
MOCK SIMULATION — NOT ANSYS RESULT. Generated by the simplified
lumped-parameter Python model, not by ANSYS.

[5] ENGINEERING SUMMARY (normalized result)
      Simulation duration       : 48.0 hours
      Minimum indoor temperature : -4.37 degC
      Maximum indoor temperature : 15.57 degC
      Average indoor temperature : 5.12 degC
      Total heat transfer        : -13705.4 Wh
      Total solar gain           : 92492.9 Wh
```

and generates three PNG plots (indoor vs. ambient temperature, heat
flow over time, surface heat-loss comparison) plus a 3-design
orientation/material comparison table.
