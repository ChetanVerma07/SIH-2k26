"""
Optional Bayesian Optimization implementation using a Gaussian Process
surrogate (scikit-learn) with an Expected-Improvement acquisition
function over the *continuous* genes. Categorical genes (materials)
are handled by randomly sampling a small candidate pool of material
combinations each iteration and letting the GP choose among the
resulting continuous-only points.

This is provided as an alternative to Differential Evolution — the
spec asks for Genetic Algorithm + (Bayesian Optimization OR
Differential Evolution). Both are implemented in this project so
results can be compared three ways.

Requires scikit-learn (see requirements.txt). Falls back gracefully
with a clear error if scikit-learn is unavailable.
"""

import random
import numpy as np

from optimizer.algorithms.design_space import (
    DEFAULT_DESIGN_SPACE, random_genome, clamp_gene, genome_to_design,
)
from optimizer.objectives.fitness import evaluate_candidate


def _continuous_keys(design_space):
    return [k for k, gd in design_space.items() if gd["type"] == "float"]


def _vectorize(genome, cont_keys):
    return np.array([genome[k] for k in cont_keys], dtype=float)


def run_bayesian_optimization(
    climate,
    evaluator,
    design_space=None,
    constraints=None,
    weights=None,
    n_initial=15,
    n_iterations=25,
    seed=42,
    top_n=5,
):
    try:
        from sklearn.gaussian_process import GaussianProcessRegressor
        from sklearn.gaussian_process.kernels import Matern, WhiteKernel
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "scikit-learn is required for Bayesian optimization. "
            "Install it via `pip install scikit-learn`."
        ) from exc

    design_space = design_space or DEFAULT_DESIGN_SPACE
    rng = random.Random(seed)
    np_rng = np.random.RandomState(seed)
    cont_keys = _continuous_keys(design_space)

    def score_of(genome):
        design = genome_to_design(genome)
        return evaluate_candidate(design, climate, evaluator, constraints, weights)

    evaluated_genomes = [random_genome(design_space, rng) for _ in range(n_initial)]
    evaluated_metrics = [score_of(g) for g in evaluated_genomes]
    all_evaluations = [(dict(g), m) for g, m in zip(evaluated_genomes, evaluated_metrics)]

    kernel = Matern(nu=2.5) + WhiteKernel(noise_level=1e-2)
    gp = GaussianProcessRegressor(kernel=kernel, normalize_y=True, random_state=seed)

    history = []

    for it in range(n_iterations):
        X = np.array([_vectorize(g, cont_keys) for g in evaluated_genomes])
        y = np.array([m["score"] for m in evaluated_metrics])
        gp.fit(X, y)

        # Generate a pool of candidate points: random continuous samples
        # combined with random categorical draws.
        candidate_pool = [random_genome(design_space, rng) for _ in range(200)]
        Xc = np.array([_vectorize(g, cont_keys) for g in candidate_pool])
        mu, sigma = gp.predict(Xc, return_std=True)

        y_best = y.max()
        with np.errstate(divide="ignore"):
            imp = mu - y_best
            z = np.where(sigma > 1e-9, imp / sigma, 0.0)
            from scipy.stats import norm
            ei = imp * norm.cdf(z) + sigma * norm.pdf(z)
            ei = np.where(sigma > 1e-9, ei, 0.0)

        best_idx = int(np.argmax(ei))
        next_genome = candidate_pool[best_idx]
        next_metrics = score_of(next_genome)

        evaluated_genomes.append(next_genome)
        evaluated_metrics.append(next_metrics)
        all_evaluations.append((dict(next_genome), next_metrics))

        scores_so_far = [m["score"] for m in evaluated_metrics]
        best_so_far = max(scores_so_far)
        avg_so_far = sum(scores_so_far) / len(scores_so_far)
        best_metrics_so_far = evaluated_metrics[scores_so_far.index(best_so_far)]

        history.append({
            "generation": it,
            "best_score": best_so_far,
            "average_score": avg_so_far,
            "best_comfort_percentage": best_metrics_so_far["comfort_percentage"],
            "best_heat_loss_kwh": best_metrics_so_far["total_heat_loss_kwh"],
        })

    ranked = sorted(zip(evaluated_genomes, evaluated_metrics),
                     key=lambda item: item[1]["score"], reverse=True)
    top_designs = [
        {"design": genome_to_design(genome), "metrics": metrics}
        for genome, metrics in ranked[:top_n]
    ]
    best_genome, best_metrics = ranked[0]

    return {
        "algorithm": "bayesian_optimization",
        "best_design": genome_to_design(best_genome),
        "best_metrics": best_metrics,
        "top_designs": top_designs,
        "history": history,
        "all_evaluations": all_evaluations,
    }
