# Phase 6 — AI-Assisted Passive Shelter Design Optimizer

**SIH 2026 — AI-Based Software Model for Designing Energy-Efficient Passive
Shelters for Different Climatic Conditions**

This is a **completely standalone** Python project. It does not import
code from any other phase, does not require a frontend, a database,
ANSYS, or any external API. It uses a lightweight, deterministic,
physics-motivated thermal model in place of ANSYS for this stage.

---

## 1. Project Purpose

Phase 6 builds the **AI / optimization intelligence** of the larger
project: given a climate, it searches the space of possible passive
shelter designs (dimensions, materials, insulation, openings,
orientation) and recommends the design that gives the best thermal
comfort with the least heat loss, least external heating energy, and
sensible material cost — while making good use of free solar energy.

## 2. The Optimization Problem

```
Climate conditions
        ↓
Generate candidate shelter designs   (design_space.py)
        ↓
Evaluate thermal performance          (thermal/simplified_model.py)
        ↓
Calculate objective score             (objectives/fitness.py)
        ↓
Optimization algorithm                (algorithms/genetic.py, differential_evolution.py, bayesian.py)
        ↓
Generate improved designs / rank       (top_designs)
        ↓
Recommend best design + explain it     (explanation/generator.py)
```

## 3. Design Variables

| Variable | Type | Example range |
|---|---|---|
| length, width | float (m) | 3.0 – 10.0 |
| height | float (m) | 2.2 – 4.0 |
| wall / roof / floor thickness | float (m) | 0.10 – 0.50 / 0.10 – 0.50 / 0.05 – 0.30 |
| insulation thickness | float (m) | 0.02 – 0.20 |
| wall / roof / floor material | categorical | see material library |
| insulation material | categorical | see material library |
| opening (window) area | derived from `opening_pct` × floor area | 2% – 30% of floor area |
| door area | float (m²) | 1.6 – 2.4 |
| orientation | float (deg) | 0 – 359 |

All ranges live in `optimizer/algorithms/design_space.py` as
`DEFAULT_DESIGN_SPACE` — change the dict, nothing else needs to change.

## 4. Constraints

Implemented in `ShelterDesign.validate()` (`optimizer/models/design.py`):
- min/max dimensions, thicknesses, door area
- min/max opening area (as a % of floor area)
- max aspect ratio (avoids absurdly long/thin shelters)
- orientation bounds

Invalid candidates are **not silently discarded** — they are scored
with a large additive penalty (`CONSTRAINT_VIOLATION_PENALTY` in
`fitness.py`) per violation, so the optimizer can still find a gradient
back into the feasible region instead of just rejecting and re-sampling
blindly.

## 5. Objective / Fitness Function

`optimizer/objectives/fitness.py`:

```
score = w_comfort   * comfort_score
      - w_heat_loss * heat_loss_score
      + w_solar     * solar_utilization_score
      - w_material  * material_cost_score
      - 50 * (number of constraint violations)
```

- `comfort_score` = fraction of the day the passive indoor temperature
  is within the climate's target comfort band.
- `heat_loss_score` / `solar_utilization_score` / `material_cost_score`
  are each normalized against a floor-area-relative reference scale
  (documented constants at the top of `fitness.py`) so the score is
  comparable across different shelter sizes. **This normalization is a
  documented heuristic choice**, not a physical law.
- Weights default to `{comfort: 1.0, heat_loss: 1.0, solar: 0.5,
  material_cost: 0.4}` (`DEFAULT_WEIGHTS`) but are fully configurable —
  pass your own `weights` dict to any algorithm or `evaluate_candidate`.
- Every candidate's raw metrics (comfort %, heat loss kWh, solar gain
  kWh, heating requirement kWh, cost index, U-values, …) are returned
  alongside the score so results are always explainable, never a black box.

## 6. Thermal Evaluator (`ThermalEvaluator` interface)

`optimizer/thermal/evaluator.py` defines an abstract interface with one
method: `evaluate(design, climate) -> metrics_dict`. The optimizer
**only ever talks to this interface**, never to a specific physics
engine. The only implementation in this phase is:

### `FastThermalEvaluator` (`optimizer/thermal/simplified_model.py`)

A quasi-steady-state, hour-by-hour model for one representative day:
1. U-values for wall/roof/floor are computed from a series-resistance
   model (material layer + insulation layer + surface films).
2. Windows/doors use fixed typical U-values (double glazing / insulated
   door).
3. Outdoor temperature follows a cosine daily cycle; solar irradiance
   follows a triangular profile over daylight hours, scaled by an
   orientation factor (cosine law, floored at 0.15 for diffuse light).
4. Each hour: passive indoor temperature = outdoor + solar_gain / UA_total.
   If that is below the comfort minimum, a "managed" indoor temperature
   (topped up to the comfort minimum) is used to compute the actual
   envelope heat loss and the heating energy required — **this is what
   makes insulation genuinely reduce heat loss and heating requirement**
   during the (typically many) hours when backup heating is needed.
5. Daily totals are integrated into kWh; comfort % = fraction of hours
   the *passive* (unheated) temperature is within the comfort band.

This model deliberately responds in the physically-correct *direction*
to every design change (see `tests/test_thermal_evaluator.py` for
explicit regression tests: more insulation → less heat loss; more
window area → more heat loss under low-solar conditions; better
orientation → more solar gain; higher-conductivity wall → more heat
loss). It is **not** a substitute for real building-physics simulation.

### Future ANSYS / ML compatibility

Because the optimizer only depends on the `ThermalEvaluator` interface,
later phases can add, without touching any optimization code:
- `ANSYSThermalEvaluator` — runs real CFD/FEA simulations per candidate.
- `MLThermalEvaluator` — wraps the surrogate model (`surrogate/model.py`)
  trained on ANSYS results, for near-instant approximate evaluation.

## 7. Optimization Algorithms

Two required algorithms are implemented, plus an optional third:

### Genetic Algorithm (`algorithms/genetic.py`)
- **population**: list of genomes (candidate designs)
- **candidate design**: one genome (flat dict of gene → value)
- **fitness**: score from `evaluate_candidate`
- **selection**: tournament selection (k=3)
- **crossover**: uniform crossover (each gene independently from parent A or B)
- **mutation**: gaussian perturbation for numeric genes, random reset for
  categorical genes, at a configurable `mutation_rate`
- **elitism**: top `elite_count` genomes always survive unchanged
- **generations**: configurable; convergence history is recorded every generation

### Differential Evolution (`algorithms/differential_evolution.py`)
Classic DE/rand/1/bin, adapted for mixed continuous/categorical genes:
- donor vector: `a + F*(b - c)` for numeric genes; random pick among
  `{a, b, c}` for categorical genes (no natural vector difference exists
  for categories)
- binomial crossover with probability `CR` (at least one gene always
  taken from the donor)
- greedy, elitist selection: trial replaces target only if it scores
  at least as well

### Bayesian Optimization (`algorithms/bayesian.py`) — optional third algorithm
Gaussian Process (Matérn kernel) surrogate over the continuous genes,
Expected-Improvement acquisition, with categorical genes resampled each
iteration from a random candidate pool. Requires scikit-learn + scipy
(already in `requirements.txt`).

All three algorithms solve the *same* problem (same design space,
fitness function and climate), so their results can be directly compared
— see `examples/ladakh_optimization.py`.

## 8. Sensitivity Analysis (`analysis/sensitivity.py`)

For the recommended design, each numeric parameter is perturbed ±15%
(orientation ±30°, clipped to stay within the design's own valid
bounds so results reflect smooth physical response rather than
constraint-boundary artifacts) and each categorical parameter is
swapped to an alternative material. The resulting change in objective
score is measured and parameters are **ranked by calculated impact** —
nothing here is a fixed/fabricated ranking.

## 9. Scenario Analysis (`analysis/scenarios.py`)

The recommended design is evaluated across multiple climate scenarios
(`optimizer/models/climate.py`: cold winter day, cold sunny day, cold
cloudy day, summer condition) to check **robustness**, not just
performance under one fixed weather pattern. Reports per-scenario
metrics, overall average score, worst-case comfort, and average heat loss.

## 10. Surrogate Model (optional, `surrogate/model.py`)

Trains a Random Forest (or Gradient Boosting) regressor on
`(design parameters) -> (comfort %, heat loss kWh)` using the
evaluation history collected during a GA/DE run, then reports mean
absolute error against a held-out set. The idea: once trained, the
surrogate can screen many more candidates than the real evaluator
(later, real ANSYS runs) could afford, cheaply narrowing down which
few designs are worth an expensive simulation. **The main optimizer
works completely independently of this — the surrogate is optional.**

## 11. Explanation Generator (`explanation/generator.py`)

Converts computed metrics into plain-language reasoning: why the top
design beat the runner-up (score, comfort, and heat-loss deltas), why
its material pairing was favored (actual conductivity values), and why
insulation thickness / orientation / opening area were set the way
they were (referencing the sensitivity-analysis ranks and % impacts
computed for that specific design). No claim is generated that isn't
backed by a computed number.

## 12. Assumptions & Limitations

- **No thermal mass / time-lag modeling.** The evaluator is
  quasi-steady per hour; it does not model how walls store and release
  heat over time. This is the single biggest simplification versus
  ANSYS and is the primary reason this evaluator is a *prototype*.
- Fixed typical U-values for windows/doors regardless of chosen frame
  materials.
- A single representative day per climate condition, not a full annual
  simulation.
- Orientation effects use a simple cosine law, not real solar-geometry
  (sun-path, latitude, shading) calculations.
- Score normalization constants (`REF_HEAT_LOSS_KWH_PER_M2`, etc.) are
  heuristic reference scales, not derived from a building code or standard.
- **This model requires engineering/ANSYS validation before being used
  for any real construction decision.**

## 13. Project Structure

```
phase6_design_optimizer/
├── optimizer/
│   ├── models/          design.py, climate.py, materials.py
│   ├── thermal/         evaluator.py (interface), simplified_model.py
│   ├── algorithms/      design_space.py, genetic.py, differential_evolution.py, bayesian.py
│   ├── objectives/      fitness.py
│   ├── analysis/        sensitivity.py, scenarios.py
│   ├── explanation/     generator.py
│   ├── surrogate/       model.py
│   └── visualization.py
├── examples/
│   └── ladakh_optimization.py
├── tests/
│   ├── test_design_and_materials.py
│   ├── test_thermal_evaluator.py
│   ├── test_fitness.py
│   ├── test_algorithms.py
│   └── test_analysis_and_explanation.py
├── requirements.txt
└── README.md
```

## 14. Installation

```bash
cd phase6_design_optimizer
pip install -r requirements.txt
```

## 15. Running the Demo

```bash
python examples/ladakh_optimization.py
```

This will: define a cold, high-altitude Ladakh climate; run the
Genetic Algorithm and Differential Evolution; compare their best
solutions; run sensitivity analysis; evaluate the winning design across
four climate scenarios; and print a full human-readable recommendation.

### Example output (abridged)

```
OPTIMIZATION COMPLETE

Recommended Design
------------------
Length: 10.0 m
Width: 10.0 m
Height: 2.2 m

Wall: stone_masonry (10.0 cm)
Roof: timber_frame (20.0 cm)
Floor: rammed_earth (23.0 cm)
Insulation: cellulose_fiber (20.0 cm)

Opening Area: 2.0 m2
Orientation: 359.0 deg

Performance
-----------
Comfort: 12.5 %
Heat Loss: 41.00 kWh/day
Solar Gain: 9.91 kWh/day
Heating Requirement: 31.10 kWh/day
Score: 0.066

WHY THIS DESIGN?
----------------
This design was selected over the next-best candidate because it scored
0.07 versus 0.06. It also lost 0.10 kWh/day less heat through the envelope.
Wall material 'stone_masonry' ... insulation 'cellulose_fiber' ...
Insulation thickness was set to 20.0 cm. Sensitivity analysis shows this
parameter has a 'high' impact on the objective score (~19.4% swing under
a ±15% perturbation), rank #1 among all analyzed parameters.
...
```

(Low winter comfort % is expected and realistic for a purely *passive*
design in a −10 °C average climate — this is exactly why the
`heating_requirement_kwh` output exists: it quantifies the backup
energy such a shelter would still need.)

### Generating visualizations

```python
from optimizer import visualization as viz
viz.plot_convergence({"GA": ga_result["history"], "DE": de_result["history"]})
viz.plot_top_designs(ga_result["top_designs"])
viz.plot_sensitivity(sensitivity_result)
viz.plot_temperature_profile(ga_result["best_metrics"])
viz.plot_scenario_comparison(scenario_result)
```

## 16. Running Tests

```bash
pytest tests/ -v
```

Tests are deterministic (fixed random seeds) and fast (small
populations/generations), covering: design validation, material
selection, constraint handling, the thermal evaluator's directional
correctness, fitness calculation, both required algorithms
(correctness + determinism + monotonic elitist improvement),
optimization output shape, sensitivity analysis, scenario analysis,
explanation generation, and the optional surrogate model.

## 17. Why ANSYS Can Later Replace `FastThermalEvaluator`

Every algorithm and analysis module in this project calls
`evaluator.evaluate(design, climate)` through the abstract
`ThermalEvaluator` interface — never `FastThermalEvaluator` directly.
To plug in real ANSYS simulations later, implement:

```python
class ANSYSThermalEvaluator(ThermalEvaluator):
    def evaluate(self, design, climate) -> dict:
        # translate design -> ANSYS input deck, run simulation,
        # parse results into the same metrics dict keys
        ...
```

and pass an instance of it wherever `FastThermalEvaluator()` is used
today. No optimizer, fitness, sensitivity, scenario, or explanation
code needs to change. Because ANSYS runs are expensive, the optional
`MLThermalEvaluator` (wrapping `surrogate/model.py`, retrained on real
ANSYS outputs) can be used for the bulk of the search, with ANSYS
itself reserved for validating only the final few top candidates.
