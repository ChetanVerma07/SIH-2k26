# Phase 1 — Passive Shelter Thermal Engine

**Part of:** "AI-Based Software Model for Designing Energy-Efficient Passive
Shelters for Different Climatic Conditions" (SIH 2026)

**This phase delivers:** a standalone, reusable Python thermal simulation
**engine only**. There is no frontend, database, API server, ANSYS
integration, cloud deployment, authentication, or external weather API in
this phase. It is designed to be imported as a library by later phases.

---

## 1. What this engine does

`thermal_engine` estimates how the indoor air temperature of a simple
rectangular passive shelter evolves over time, given:

- outdoor (ambient) air temperature — constant or time-varying,
- incident solar radiation — constant or time-varying,
- shelter geometry (length, width, height, openings),
- the materials used for the walls, roof and floor,
- an initial indoor temperature,
- a simulation duration and timestep.

It reports, at every timestep: conductive heat loss through walls, roof,
floor and openings; solar heat gain; net heat flow; and the resulting
indoor temperature — plus summary metrics (min/max/average indoor
temperature, total energy gained/lost, and time spent within a target
"comfort range").

It also lets you simulate **several shelter designs side-by-side** under
identical weather conditions, to compare which performs better — the data
foundation a future optimisation engine will search over.

## 2. Why it is being developed

Communities in extreme climates (e.g. cold, high-altitude regions like
Ladakh) need shelters that stay liveable with minimal active heating or
cooling. Deciding on wall thickness, insulation, glazing, and orientation
by trial and error — or by jumping straight to a full ANSYS CFD model — is
slow and expensive. This engine is a fast, dependency-light "first pass"
that lets a designer (or, later, an automated optimiser) quickly compare
many design options and narrow down candidates worth a full, high-fidelity
simulation.

## 3. Input parameters

| Parameter | Where | Unit | Notes |
|---|---|---|---|
| `ambient_temperature` | `simulate_shelter` | °C | constant or time series |
| `solar_radiation` | `simulate_shelter` | W/m² | constant or time series, ≥ 0 |
| `duration_hours` | `simulate_shelter` | h | total simulated time |
| `time_step_hours` | `simulate_shelter` | h | simulation resolution |
| `comfort_range` | `simulate_shelter` / `Shelter` | (°C, °C) | optional |
| `length`, `width`, `height` | `Shelter` | m | footprint + wall height |
| `wall_material`, `roof_material`, `floor_material` | `Shelter` | `Material` | |
| `num_openings`, `opening_area_each` | `Shelter` | count, m² | windows/doors |
| `opening_u_value` | `Shelter` | W/(m²·K) | lumped glazing/door U-value |
| `initial_indoor_temperature` | `Shelter` | °C | starting condition |
| `solar_wall_fraction` | `Shelter` | 0–1 | fraction of wall assumed sun-lit |
| `thermal_conductivity`, `density`, `specific_heat`, `thickness`, `solar_absorptivity`, `emissivity` | `Material` | SI / 0–1 | per material layer |

## 4. Thermal equations used

All calculations use SI units (temperatures in °C are fine since only
temperature *differences* enter the equations).

**Conductive heat flow through a surface:**

```
Q = U * A * (T_indoor - T_outdoor)
```

`Q > 0` means the shelter is losing heat to the outside.

**Surface U-value** (per opaque surface — wall, roof, floor):

```
U = 1 / (R_film + thickness / k)
```

where `thickness / k` is the material's conductive resistance and
`R_film` (`SURFACE_FILM_RESISTANCE = 0.17 m²·K/W`) is a standard combined
indoor+outdoor air-film resistance (see *Assumptions* below — this is what
keeps, e.g., a thin sheet-metal roof physically and numerically sane).
Opening U-values are supplied directly by the user as a single overall
value (typical practice for windows/doors).

**Solar heat gain:**

```
Q_solar = solar_radiation * effective_area * solar_absorptivity
```

**Indoor temperature update** (explicit-Euler, lumped thermal mass):

```
net_heat_flow = Q_solar - (Q_wall + Q_roof + Q_floor + Q_opening)
dT            = net_heat_flow * dt / C
T_indoor      = T_indoor + dT
```

where `C` is the shelter's total thermal capacity (J/K), built from each
material's `density * thickness * specific_heat * area`.

## 5. Assumptions and limitations

This is a **simplified, single-node (lumped-capacitance) model** for early
design comparison — **it is not, and is not claimed to be, equivalent to a
full ANSYS CFD/finite-element thermal simulation.** Specifically:

- **One indoor temperature node.** The whole interior (air + fabric) is
  treated as a single uniform temperature. No spatial gradients, no
  separate air/wall-surface temperatures, no room-to-room variation.
- **Rectangular box geometry only.** Flat roof, four walls, single floor
  slab. No pitched roofs, no complex plans, no multiple thermal zones.
- **Single-layer materials.** Each surface (wall/roof/floor) uses one
  material's properties. A real composite wall (e.g. brick + insulation)
  must be approximated as one "effective" material for this phase (see
  `examples/basic_simulation.py`, Design C, for how that's done) — proper
  multi-layer/series-resistance walls are a natural Phase 2 extension.
  When you provide values for this effective layer, the individual material
  properties should each remain physically valid (positive conductivity,
  thickness, etc.); it is only the *combination* that is being
  approximated as one layer, not a physical claim about that exact
  material existing.
- **Standard combined surface film resistance.** A single
  `SURFACE_FILM_RESISTANCE = 0.17 m²·K/W` (a representative combined
  indoor+outdoor convective film value) is added in series with every
  opaque surface's material resistance, rather than the full
  orientation/airflow-specific table used in detailed building-physics
  references (e.g. ISO 6946). Without this, a thin, highly conductive
  material (like a bare metal sheet) produces an unrealistically huge
  U-value that is both physically wrong and numerically unstable.
- **Floor treated like the other surfaces.** Floor heat loss is computed
  against the *ambient air* temperature via the same `Q = U*A*ΔT` formula,
  not against ground temperature (which is usually more stable and
  different from air temperature). This is a known simplification to
  revisit in a later phase.
- **No long-wave (night-sky) radiation exchange.** Material `emissivity`
  is captured on the `Material` model for forward-compatibility but is not
  yet used in the heat-balance equations — only solar (short-wave) gain
  and conduction are modelled in Phase 1.
- **No infiltration/ventilation modelling.** Air leakage through gaps and
  intentional ventilation are not modelled; `opening_heat_loss` covers
  conduction through the closed window/door area only.
- **No internal heat gains.** Occupants, appliances, and any active
  heating/cooling are not modelled — this is a purely passive analysis.
- **Explicit-Euler time integration.** Simple and transparent, but can
  become inaccurate (and in extreme cases unstable) for very large
  timesteps relative to the shelter's thermal time constant. Prefer
  timesteps of 1 hour or smaller unless you've checked stability for your
  own material choices.
- **Solar gain is simplified.** All solar radiation is treated as landing
  on one "effective sun-exposed area" using the roof material's
  absorptivity; there's no true-position sun-angle, shading, or per-facade
  orientation model.

## 6. How the simulation works

1. `Shelter.__post_init__` validates geometry and computes derived
   quantities (areas, U-values, thermal capacity) — see `shelter.py`.
2. `simulate_shelter(...)` (`simulation.py`):
   - Normalises `ambient_temperature` / `solar_radiation` onto the
     simulation's timestep grid (`_resample_to_steps`) — a constant is
     broadcast, and a time series of any length is linearly resampled
     (via `numpy.interp`) onto the requested number of steps, so e.g. 24
     hourly readings can drive a 15-minute-timestep run.
   - Loops over each timestep, calling the pure functions in `physics.py`
     to compute wall/roof/floor/opening conduction and solar gain, sums
     them into `net_heat_flow`, and updates indoor temperature.
   - Returns a `SimulationResult` with a full per-timestep
     `pandas.DataFrame` (`.timeseries`) and a summary `dict` (`.summary`).
3. `compare_designs(...)` (`comparison.py`) runs `simulate_shelter` once
   per design under identical conditions and returns one comparison
   `pandas.DataFrame`, sorted by average indoor temperature.

## 7. How to create custom materials

```python
from thermal_engine import Material

my_insulation = Material(
    name="Custom Aerogel Panel",
    thermal_conductivity=0.02,   # W/(m.K)
    density=150.0,               # kg/m^3
    specific_heat=1000.0,        # J/(kg.K)
    thickness=0.05,              # m
    solar_absorptivity=0.4,      # 0-1
    emissivity=0.9,              # 0-1, optional (default 0.9)
)
```

Invalid values (non-positive conductivity/density/specific_heat/thickness,
or absorptivity/emissivity outside `[0, 1]`) raise
`ThermalEngineValidationError` with a clear message. Prebuilt example
materials live in `thermal_engine.EXAMPLE_MATERIALS` (mud adobe, rammed
earth, fired brick, concrete, rock wool, EPS, timber, corrugated iron
sheet, straw bale) — inspect `thermal_engine/materials.py` for the full
list and values.

## 8. How to create custom shelter designs

```python
from thermal_engine import Material, Shelter, EXAMPLE_MATERIALS

my_shelter = Shelter(
    name="My Design",
    length=6.0, width=4.0, height=2.8,          # m
    wall_material=EXAMPLE_MATERIALS["rammed_earth"],
    roof_material=EXAMPLE_MATERIALS["timber_plank"],
    floor_material=EXAMPLE_MATERIALS["concrete"],
    num_openings=2, opening_area_each=1.2,       # m^2 each
    opening_u_value=2.8,                          # W/(m^2.K)
    initial_indoor_temperature=5.0,               # C
    comfort_range=(15.0, 24.0),                   # optional, C
)
```

Invalid geometry (negative dimensions, openings larger than the wall,
etc.) raises `ThermalEngineValidationError` or `ValueError` with a clear
message.

## 9. How to run the demo

```bash
pip install -r requirements.txt
python main.py
```

(equivalently: `python examples/basic_simulation.py`)

This runs a 24-hour, cold, high-altitude scenario (illustrative
Ladakh-like example weather values — not real measured data) and:

1. prints a detailed report for a baseline uninsulated design,
2. compares three designs (baseline mud adobe / rammed earth / insulated)
   under the same conditions and prints a ranked comparison table.

## 10. How to run tests

```bash
pip install -r requirements.txt
pytest
```

or, to see individual test names:

```bash
pytest -v
```

`tests/` covers: material creation and validation, physics formulas
(conduction, solar gain, temperature update), shelter geometry
calculations, full simulation execution (constant and time-series
inputs, including automatic resampling of mismatched series lengths),
indoor temperature evolving correctly over time in both cold and hot
ambient scenarios, summary/comfort-range metrics, input validation
errors, and multi-design comparison.

> **Note on this sandbox:** the code above was verified to run correctly
> in the environment that produced it, including all 41 tests, using a
> minimal pytest-compatible test runner (this sandbox has no network
> access to `pip install pytest` itself). Please still run the real
> `pytest` locally as shown above — it's a standard, well-known tool and
> will behave identically.

## 11. Project structure

```
phase1_thermal_engine/
├── thermal_engine/
│   ├── __init__.py       # public API (Material, Shelter, simulate_shelter, compare_designs, ...)
│   ├── materials.py       # Material model + EXAMPLE_MATERIALS
│   ├── shelter.py         # Shelter geometry/config model
│   ├── physics.py         # pure heat-transfer formulas
│   ├── simulation.py       # transient simulation loop + SimulationResult
│   ├── comparison.py       # multi-design comparison utility
│   └── validation.py       # shared input-validation helpers
├── examples/
│   └── basic_simulation.py # Ladakh-like 24h demo + 3-design comparison
├── tests/
│   ├── test_materials.py
│   ├── test_physics.py
│   └── test_simulation.py  # covers Shelter, simulate_shelter, compare_designs
├── requirements.txt
├── README.md
└── main.py                 # `python main.py` runs the demo
```

**Why plain `dataclasses` instead of Pydantic:** the brief allowed Pydantic
"if useful." This phase's core models are simple, immutable, in-memory
value objects with straightforward numeric validation — plain
`@dataclass(frozen=True)` plus the shared functions in `validation.py`
meets that need without adding an external dependency to the core
physics/geometry code. `pytest` remains a (test-time only) dependency, as
requested. If a later phase's API/backend layer wants request/response
validation, Pydantic models can wrap these dataclasses at that boundary
without changing the engine itself.

## 12. Connecting this to later phases (not built here)

- **ANSYS integration:** this engine's `Shelter`/`Material` inputs and
  `SimulationResult` outputs are deliberately plain, serialisable Python
  objects, so a later phase could either (a) use this engine for fast
  pre-screening and only send shortlisted designs to ANSYS for
  high-fidelity validation, or (b) swap this engine's `simulate_shelter`
  implementation for an ANSYS-backed one behind the same function
  signature. No ANSYS API details are assumed or invented here.
- **Weather-data integration:** `simulate_shelter` already accepts any
  list/array/Series of ambient temperature and solar radiation, so a
  future weather-API layer just needs to produce data in that shape.
- **API/backend:** `thermal_engine` has no I/O, no global state, and no
  web-framework dependency, so it can be imported directly into a
  FastAPI/Flask/Django service and called per-request.
- **Optimisation:** `compare_designs` is the "evaluate a batch of designs"
  primitive an optimiser (grid search, genetic algorithm, Bayesian
  optimisation, etc.) would call repeatedly while varying materials and
  geometry — no search/optimisation logic is implemented in this phase.
- **ML surrogate modelling:** because `simulate_shelter` is deterministic
  and fast, it can generate labelled (design → performance) training data
  for a future surrogate model, without needing this engine itself to use
  any ML/AI libraries.
- **Frontend/visualisation:** `SimulationResult.timeseries` is a standard
  `pandas.DataFrame`, directly usable by any plotting/reporting layer
  (e.g. Plotly, Matplotlib, a web frontend via JSON) added in a later
  phase.
