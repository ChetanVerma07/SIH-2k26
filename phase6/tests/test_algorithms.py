import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from optimizer.models.climate import SCENARIOS
from optimizer.thermal.simplified_model import FastThermalEvaluator
from optimizer.algorithms.genetic import run_genetic_algorithm
from optimizer.algorithms.differential_evolution import run_differential_evolution

CLIMATE = SCENARIOS["cold_winter_day"]


def test_genetic_algorithm_runs_and_returns_expected_shape():
    evaluator = FastThermalEvaluator()
    result = run_genetic_algorithm(
        CLIMATE, evaluator, population_size=12, generations=5, seed=7, top_n=3,
    )
    assert "best_design" in result
    assert "best_metrics" in result
    assert len(result["top_designs"]) == 3
    assert len(result["history"]) == 5
    for h in result["history"]:
        assert "best_score" in h and "average_score" in h


def test_genetic_algorithm_improves_over_generations():
    evaluator = FastThermalEvaluator()
    result = run_genetic_algorithm(
        CLIMATE, evaluator, population_size=16, generations=12, seed=3,
    )
    first_gen_best = result["history"][0]["best_score"]
    last_gen_best = result["history"][-1]["best_score"]
    assert last_gen_best >= first_gen_best  # elitism guarantees monotonic improvement


def test_genetic_algorithm_is_deterministic_given_seed():
    evaluator = FastThermalEvaluator()
    r1 = run_genetic_algorithm(CLIMATE, evaluator, population_size=10, generations=4, seed=99)
    r2 = run_genetic_algorithm(CLIMATE, evaluator, population_size=10, generations=4, seed=99)
    assert r1["best_metrics"]["score"] == r2["best_metrics"]["score"]


def test_differential_evolution_runs_and_returns_expected_shape():
    evaluator = FastThermalEvaluator()
    result = run_differential_evolution(
        CLIMATE, evaluator, population_size=12, generations=5, seed=7, top_n=3,
    )
    assert "best_design" in result
    assert len(result["top_designs"]) == 3
    assert len(result["history"]) == 5


def test_differential_evolution_is_elitist_non_decreasing():
    evaluator = FastThermalEvaluator()
    result = run_differential_evolution(
        CLIMATE, evaluator, population_size=14, generations=10, seed=5,
    )
    scores = [h["best_score"] for h in result["history"]]
    assert all(scores[i] <= scores[i + 1] + 1e-9 for i in range(len(scores) - 1))
