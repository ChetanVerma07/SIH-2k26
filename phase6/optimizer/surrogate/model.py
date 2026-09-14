"""
Optional ML surrogate experiment.

Idea: the thermal evaluator (or later, real ANSYS simulations) is
expensive. If we can train a fast regression model to predict the
evaluator's outputs from design parameters, we can screen thousands of
candidates cheaply and only run the expensive evaluator on the most
promising ones. This module is entirely optional; the main
optimizers (GA / DE / Bayesian) work without it and do not depend on
it in any way.

Usage:
    surrogate = ThermalSurrogate()
    surrogate.fit(all_evaluations)   # from a GA/DE run's `all_evaluations`
    report = surrogate.evaluate_against_ground_truth(held_out_evaluations)
"""

import numpy as np

CONTINUOUS_GENE_KEYS = [
    "length", "width", "height", "wall_thickness", "roof_thickness",
    "floor_thickness", "insulation_thickness", "opening_pct", "door_area", "orientation",
]


class ThermalSurrogate:
    """Wraps a scikit-learn regressor to predict `comfort_percentage` and
    `total_heat_loss_kwh` from a design's continuous parameters."""

    def __init__(self, model_type="random_forest", seed=42):
        self.model_type = model_type
        self.seed = seed
        self.comfort_model = None
        self.heat_loss_model = None
        self._is_fitted = False

    def _build_model(self):
        if self.model_type == "random_forest":
            from sklearn.ensemble import RandomForestRegressor
            return RandomForestRegressor(n_estimators=100, random_state=self.seed)
        elif self.model_type == "gradient_boosting":
            from sklearn.ensemble import GradientBoostingRegressor
            return GradientBoostingRegressor(random_state=self.seed)
        raise ValueError(f"Unsupported model_type: {self.model_type}")

    @staticmethod
    def _vectorize(genome: dict) -> list:
        return [genome[k] for k in CONTINUOUS_GENE_KEYS]

    def fit(self, evaluations: list):
        """evaluations: list of (genome_dict, metrics_dict) tuples, e.g.
        taken directly from a GA/DE run's `all_evaluations` output."""
        X = np.array([self._vectorize(g) for g, _ in evaluations])
        y_comfort = np.array([m["comfort_percentage"] for _, m in evaluations])
        y_heatloss = np.array([m["total_heat_loss_kwh"] for _, m in evaluations])

        self.comfort_model = self._build_model()
        self.heat_loss_model = self._build_model()
        self.comfort_model.fit(X, y_comfort)
        self.heat_loss_model.fit(X, y_heatloss)
        self._is_fitted = True
        return self

    def predict(self, genome: dict) -> dict:
        if not self._is_fitted:
            raise RuntimeError("Surrogate model has not been fitted yet.")
        x = np.array([self._vectorize(genome)])
        return {
            "predicted_comfort_percentage": float(self.comfort_model.predict(x)[0]),
            "predicted_total_heat_loss_kwh": float(self.heat_loss_model.predict(x)[0]),
        }

    def evaluate_against_ground_truth(self, held_out_evaluations: list) -> dict:
        """Compare surrogate predictions to the actual evaluator's output on
        a held-out set. Returns mean absolute error for both targets."""
        if not self._is_fitted:
            raise RuntimeError("Surrogate model has not been fitted yet.")

        comfort_errors = []
        heatloss_errors = []
        for genome, metrics in held_out_evaluations:
            pred = self.predict(genome)
            comfort_errors.append(abs(pred["predicted_comfort_percentage"] - metrics["comfort_percentage"]))
            heatloss_errors.append(abs(pred["predicted_total_heat_loss_kwh"] - metrics["total_heat_loss_kwh"]))

        return {
            "n_samples": len(held_out_evaluations),
            "mean_absolute_error_comfort_pct": float(np.mean(comfort_errors)) if comfort_errors else None,
            "mean_absolute_error_heat_loss_kwh": float(np.mean(heatloss_errors)) if heatloss_errors else None,
        }
