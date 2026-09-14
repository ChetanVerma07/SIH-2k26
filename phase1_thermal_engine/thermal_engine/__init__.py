"""
thermal_engine
==============

Standalone thermal simulation engine for energy-efficient passive shelter
design (Phase 1 of the SIH 2026 project).

Public API:

    from thermal_engine import Material, Shelter, simulate_shelter
    from thermal_engine import compare_designs, EXAMPLE_MATERIALS

    results = simulate_shelter(shelter, ambient_temperature=-10,
                                solar_radiation=400, duration_hours=24)
    print(results.summary)
    results.timeseries.head()

See the project README for the full physics model, assumptions and
limitations.
"""

from .comparison import compare_designs
from .materials import EXAMPLE_MATERIALS, Material
from .shelter import Shelter
from .simulation import SimulationResult, simulate_shelter
from .validation import ThermalEngineValidationError

__all__ = [
    "Material",
    "EXAMPLE_MATERIALS",
    "Shelter",
    "simulate_shelter",
    "SimulationResult",
    "compare_designs",
    "ThermalEngineValidationError",
]

__version__ = "0.1.0"
