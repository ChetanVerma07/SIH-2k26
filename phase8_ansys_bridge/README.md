# Phase 8 -- Software-to-ANSYS Simulation Bridge

**Project:** AI-Based Software Model for Designing Energy-Efficient Passive
Shelters for Different Climatic Conditions
**Phase:** 8 of N -- independent, standalone module.

This phase does **not** depend on any earlier phase's code, frontend,
database, or a live weather API. It is a pure Python package you can run
right now with `python demo.py`.

## What it does

1. Accepts shelter design parameters (`ShelterDesignParams`) and climate
   parameters (`ClimateParams`).
2. Generates a real, hand-off-ready **ANSYS Mechanical APDL** batch input
   file (`shelter_thermal.inp`) -- transient thermal analysis of the
   envelope (walls, roof, windows) with time-varying ambient/solar loads.
3. Manages simulation "cases" on disk (`core/case_manager.py`) -- no
   database needed.
4. Runs the simulation through a **configurable backend interface**
   (`SimulationBackend`):
   - `MockANSYSBackend` -- always available, synthesizes a physically
     grounded result (same envelope physics as the simplified model, plus
     an independent thermal-bridging correction + noise) so the whole
     pipeline can be demoed/tested with **zero ANSYS install**.
   - `ANSYSBackend` -- calls a real MAPDL executable in batch mode
     (`mapdl -b -np <cores> -i case.inp -o case.out`), fully configurable
     (executable path, cores, license server, timeout). If ANSYS isn't
     found, it fails fast with a clear message -- but the `.inp` file has
     **already been written**, so you always get the ANSYS-ready input
     even if the run itself can't happen on this machine.
5. Imports results (CSV: `time_s, indoor_temp_c, heat_flux_w_m2`) from
   either backend.
6. Extracts thermal performance metrics: peak/mean/min indoor temp,
   swing, decrement factor, thermal lag, comfort-band coverage, peak heat
   flux, total heat gain.
7. Runs an **independent simplified thermal model** (lumped-capacitance /
   RC network, analytic per-step update) re-implemented from scratch in
   this phase -- no import from earlier phases.
8. Compares ANSYS-backend metrics against the simplified model
   (per-metric % deviation, indoor-temp RMSE, correlation).
9. Validates the design against climate-zone-specific expectations
   (decrement factor ceiling, minimum thermal lag, comfort coverage,
   ANSYS/simplified agreement) with PASS / WARNING / FAIL verdicts.
10. Produces a structured report (`report.json` + `report.md`) per case.

## Architecture

```
SimulationBackend (abstract)
        |
   -----------------
   |               |
MockANSYSBackend  ANSYSBackend
(always on,       (real MAPDL batch run,
 synthetic run)    configurable, fails fast
                    if ANSYS isn't installed)
```

Both backends share `core/input_generator.py` (APDL file generation) and
`core/envelope_physics.py` (UA / thermal capacitance / solar-gain
formulas), so the `.inp` file and the physics behind Mock results are
consistent with each other and with the simplified model.

## Directory layout

```
phase8_ansys_bridge/
  config.py                    Design / climate / settings dataclasses
  pipeline.py                  Phase8Pipeline -- runs the full flow for one case
  demo.py                      Runnable end-to-end demo (2 sample cases)
  backend/
    simulation_backend.py      SimulationBackend abstract interface
    mock_backend.py            MockANSYSBackend
    ansys_backend.py           ANSYSBackend (real MAPDL integration)
  core/
    input_generator.py         Builds the ANSYS APDL (.inp) file
    envelope_physics.py         Shared UA / capacitance / solar-gain helpers
    case_manager.py             Case creation, status tracking, on-disk storage
    results_importer.py         Parses ANSYS/mock result CSVs
    metrics_extractor.py        Computes thermal performance metrics
    simplified_thermal_model.py Independent lumped-capacitance model
    comparator.py                ANSYS vs simplified model comparison
    validator.py                 Rule-based design validation
    report_generator.py          JSON + Markdown report writer
  simulation_cases/            Created at runtime, one folder per case
```

## Running it

```bash
python demo.py
```

This runs two sample hot-dry-climate cases (a thin-wall baseline vs. a
thick, insulated, shaded, high-mass "improved" design) through the full
pipeline using `MockANSYSBackend`, prints a summary, and writes full
reports to `simulation_cases/<case_id>/`.

## Using a real ANSYS install

```python
from backend.ansys_backend import ANSYSBackend
from pipeline import Phase8Pipeline

backend = ANSYSBackend(
    exe_path="mapdl",          # or full path to the MAPDL executable
    num_cores=4,
    license_server=None,       # e.g. "1055@license-server" if needed
    timeout_s=1800,
)
pipeline = Phase8Pipeline(backend=backend)
report = pipeline.run_case(design, climate, settings)
```

If ANSYS isn't found or the solve fails, `report["status"] == "failed"`
and `report["input_file"]` still points at a valid `.inp` file you can
hand to a licensed workstation -- nothing is lost.

## Requirements

Pure Python 3.8+ standard library only. No `pip install` needed.
