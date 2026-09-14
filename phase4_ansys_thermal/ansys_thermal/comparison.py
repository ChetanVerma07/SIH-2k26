"""
Design comparison utility.

Runs (or prepares) multiple simulation configurations and returns a
comparable set of thermal metrics for each. This does NOT implement
the final AI-driven optimizer (that belongs to a later phase) — it is
a straightforward batch-runner + metrics table intended to be a
building block for that optimizer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Sequence

from ansys_thermal.models.simulation import SimulationConfig
from ansys_thermal.ansys.adapter import ThermalSimulationAdapter, MockThermalAdapter
from ansys_thermal.validation.validators import validate_simulation_config


@dataclass
class DesignResult:
    design_name: str
    normalized_result: Dict[str, Any]

    def metrics(self) -> Dict[str, Any]:
        s = self.normalized_result["summary"]
        sr = self.normalized_result["surface_results"]
        return {
            "design_name": self.design_name,
            "min_temp_c": s["min_temp_c"],
            "max_temp_c": s["max_temp_c"],
            "avg_temp_c": s["avg_temp_c"],
            "total_heat_transfer_wh": s["total_heat_transfer_wh"],
            "total_solar_gain_wh": s["total_solar_gain_wh"],
            "wall_heat_transfer_wh": sr["wall_heat_transfer_wh"],
            "roof_heat_transfer_wh": sr["roof_heat_transfer_wh"],
            "floor_heat_transfer_wh": sr["floor_heat_transfer_wh"],
            "opening_heat_transfer_wh": sr["opening_heat_transfer_wh"],
            "is_mock": self.normalized_result["meta"]["is_mock"],
        }


def compare_designs(
    configs: Sequence[SimulationConfig],
    adapter_factory=MockThermalAdapter,
) -> List[DesignResult]:
    """Validate, run, and normalize a set of design configurations.

    Parameters
    ----------
    configs: a sequence of SimulationConfig objects, each representing
        one design variant (e.g. different material, orientation).
    adapter_factory: a callable taking a SimulationConfig and
        returning a ThermalSimulationAdapter instance. Defaults to
        MockThermalAdapter so comparisons work without ANSYS. Pass a
        factory wrapping AnsysThermalAdapter to compare designs using
        real ANSYS runs instead (once available).

    Returns
    -------
    List of DesignResult, one per input config, in the same order.
    """
    results: List[DesignResult] = []
    for config in configs:
        validate_simulation_config(config)
        adapter: ThermalSimulationAdapter = adapter_factory(config)
        normalized = adapter.run_full_workflow()
        results.append(DesignResult(design_name=config.name, normalized_result=normalized))
    return results


def metrics_table(design_results: Sequence[DesignResult]) -> List[Dict[str, Any]]:
    """Return a list of flat metric dicts, one per design, suitable
    for printing as a table or feeding into pandas/a future optimizer.
    """
    return [dr.metrics() for dr in design_results]
