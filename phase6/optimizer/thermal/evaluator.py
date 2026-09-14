"""
ThermalEvaluator interface.

The optimizer NEVER talks to a specific physics engine directly — it
only calls `evaluate(design, climate)` on whatever object implements
this interface. That is what allows a future, much more expensive
`ANSYSThermalEvaluator` (running real CFD/FEA simulations) or an
`MLThermalEvaluator` (a trained surrogate) to be substituted in without
touching a single line of the optimization algorithms.

Required output dict keys (all evaluators must return these):
    avg_indoor_temp_c
    min_indoor_temp_c
    max_indoor_temp_c
    comfort_percentage        (0-100)
    total_heat_loss_kwh       (per simulated day)
    total_solar_gain_kwh      (per simulated day)
    heating_requirement_kwh   (energy needed to keep design within comfort band)
    hourly_indoor_temp        (list[24] of floats, for plotting/analysis)
"""

from abc import ABC, abstractmethod


class ThermalEvaluator(ABC):
    @abstractmethod
    def evaluate(self, design, climate) -> dict:
        """Evaluate one ShelterDesign under one ClimateCondition.

        Returns a dict of performance metrics (see module docstring for
        the required keys). Implementations must be deterministic given
        the same (design, climate) input.
        """
        raise NotImplementedError
