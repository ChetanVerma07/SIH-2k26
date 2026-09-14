"""
Phase 8 - Configuration models.

Independent, self-contained data structures describing:
  - the passive shelter design (geometry + envelope materials)
  - the climate / environmental conditions to simulate against
  - the simulation run settings (mesh, solver, ANSYS-specific knobs)

No dependency on any earlier phase. Pure dataclasses + stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class ClimateZone(str, Enum):
    HOT_DRY = "hot_dry"
    WARM_HUMID = "warm_humid"
    COMPOSITE = "composite"
    TEMPERATE = "temperate"
    COLD = "cold"


class AnalysisType(str, Enum):
    STEADY_STATE = "steady_state"
    TRANSIENT = "transient"


class SolverBackendType(str, Enum):
    MOCK = "mock"
    ANSYS = "ansys"


@dataclass
class ShelterDesignParams:
    """Envelope + geometry description of the passive shelter."""

    design_id: str
    wall_material: str = "fired_brick"
    wall_thickness_m: float = 0.23
    wall_conductivity_w_mk: float = 0.71
    roof_material: str = "rcc_slab"
    roof_thickness_m: float = 0.15
    roof_conductivity_w_mk: float = 1.58
    insulation_r_value_m2k_w: float = 0.0  # added insulation, if any
    wall_area_m2: float = 90.0
    roof_area_m2: float = 45.0
    floor_area_m2: float = 45.0
    window_area_m2: float = 6.0
    window_u_value_w_m2k: float = 2.8
    orientation_deg: float = 180.0  # 0 = north facing main facade
    thermal_mass_class: str = "medium"  # low | medium | high
    shading_coefficient: float = 0.8  # 1.0 = no shading, lower = more shading
    ventilation_ach: float = 1.0  # air changes per hour
    num_occupants: int = 4
    internal_gains_w: float = 300.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ClimateParams:
    """Environmental boundary conditions for the simulation window."""

    location_name: str
    climate_zone: ClimateZone
    ambient_temp_profile_c: list = field(
        default_factory=lambda: [24, 23, 22, 22, 21, 22, 24, 27, 30, 33,
                                  35, 37, 38, 38, 37, 36, 34, 31, 29, 27,
                                  26, 25, 24, 24]
    )  # 24 hourly values, index 0 = 00:00
    solar_radiation_profile_w_m2: list = field(
        default_factory=lambda: [0, 0, 0, 0, 0, 50, 150, 300, 500, 650,
                                  780, 850, 870, 830, 720, 560, 380, 180,
                                  40, 0, 0, 0, 0, 0]
    )
    relative_humidity_pct: float = 35.0
    wind_speed_m_s: float = 2.5
    ground_temp_c: float = 26.0
    altitude_m: float = 216.0
    season: str = "summer"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["climate_zone"] = self.climate_zone.value
        return d


@dataclass
class SimulationSettings:
    """Numerical / backend configuration for the run."""

    analysis_type: AnalysisType = AnalysisType.TRANSIENT
    duration_hours: int = 24
    time_step_s: int = 900  # 15 minutes
    mesh_element_size_m: float = 0.05
    convergence_tolerance: float = 1e-4
    solver_backend: SolverBackendType = SolverBackendType.MOCK
    comfort_band_low_c: float = 18.0
    comfort_band_high_c: float = 30.0
    deviation_tolerance_pct: float = 15.0  # ANSYS vs simplified model tolerance

    # ANSYS-specific (only used by ANSYSBackend, harmless otherwise)
    ansys_exe_path: Optional[str] = None  # e.g. "ansys2024R1" or full path to MAPDL
    ansys_working_dir: Optional[str] = None
    ansys_num_cores: int = 2
    ansys_license_server: Optional[str] = None
    ansys_timeout_s: int = 1800

    def to_dict(self) -> dict:
        d = asdict(self)
        d["analysis_type"] = self.analysis_type.value
        d["solver_backend"] = self.solver_backend.value
        return d
