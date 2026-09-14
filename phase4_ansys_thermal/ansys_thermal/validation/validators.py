"""
Validation utilities.

These functions check that user-supplied configuration values are
physically plausible before they are used to build ANSYS input or run
the mock adapter. They raise ``ValidationError`` (defined here) with a
clear, specific message on failure. Nothing here silently "fixes" bad
data by substituting invented values — invalid input is rejected.
"""

from __future__ import annotations

from typing import List

from ansys_thermal.models.geometry import ShelterGeometry
from ansys_thermal.models.materials import Material, MaterialAssignment
from ansys_thermal.models.climate import BoundaryConditions


class ValidationError(ValueError):
    """Raised when a configuration value is physically invalid or
    outside a documented sane range."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def validate_geometry(geometry: ShelterGeometry) -> None:
    _require(geometry.length > 0, "geometry.length must be > 0 m")
    _require(geometry.width > 0, "geometry.width must be > 0 m")
    _require(geometry.height > 0, "geometry.height must be > 0 m")

    _require(geometry.wall_thickness > 0, "geometry.wall_thickness must be > 0 m")
    _require(geometry.roof_thickness > 0, "geometry.roof_thickness must be > 0 m")
    _require(geometry.floor_thickness > 0, "geometry.floor_thickness must be > 0 m")

    _require(
        geometry.wall_thickness < min(geometry.length, geometry.width) / 2,
        "geometry.wall_thickness is too large relative to length/width "
        "(walls would meet in the middle)",
    )

    for name, val in (
        ("window_area", geometry.window_area),
        ("door_area", geometry.door_area),
        ("other_openings_area", geometry.other_openings_area),
    ):
        _require(val >= 0, f"geometry.{name} must be >= 0 m^2")

    gross_wall_area = geometry.wall_gross_area()
    total_openings = geometry.total_opening_area()
    _require(
        total_openings <= gross_wall_area,
        f"Total opening area ({total_openings:.2f} m^2) exceeds gross wall "
        f"area ({gross_wall_area:.2f} m^2)",
    )

    _require(
        0.0 <= geometry.orientation_deg < 360.0,
        "geometry.orientation_deg must be in [0, 360)",
    )

    # Sanity bounds to catch obvious unit-entry mistakes (e.g. metres
    # entered as millimetres). These are generous engineering bounds,
    # not hard physical limits.
    _require(geometry.length <= 200, "geometry.length exceeds 200 m sanity bound")
    _require(geometry.width <= 200, "geometry.width exceeds 200 m sanity bound")
    _require(geometry.height <= 50, "geometry.height exceeds 50 m sanity bound")


def validate_material(material: Material, label: str = "material") -> None:
    _require(
        material.thermal_conductivity_w_mk > 0,
        f"{label}.thermal_conductivity_w_mk must be > 0",
    )
    _require(material.density_kg_m3 > 0, f"{label}.density_kg_m3 must be > 0")
    _require(
        material.specific_heat_j_kgk > 0, f"{label}.specific_heat_j_kgk must be > 0"
    )
    _require(
        0.0 <= material.emissivity <= 1.0, f"{label}.emissivity must be in [0, 1]"
    )
    _require(
        0.0 <= material.solar_absorptivity <= 1.0,
        f"{label}.solar_absorptivity must be in [0, 1]",
    )


def validate_material_assignment(assignment: MaterialAssignment) -> None:
    validate_material(assignment.wall_material, "wall_material")
    validate_material(assignment.roof_material, "roof_material")
    validate_material(assignment.floor_material, "floor_material")
    validate_material(assignment.window_material, "window_material")


def validate_boundary_conditions(bc: BoundaryConditions) -> None:
    _require(len(bc.ambient_series) >= 2, "ambient_series must have at least 2 points")

    _require(bc.time_step_s > 0, "time_step_s must be > 0")
    _require(bc.duration_hours > 0, "duration_hours must be > 0")

    max_steps = 200_000  # sanity bound to avoid runaway simulations
    n_steps = int(round((bc.duration_hours * 3600.0) / bc.time_step_s))
    _require(
        n_steps <= max_steps,
        f"Requested duration/time_step implies {n_steps} steps, "
        f"exceeding sanity bound of {max_steps}. Increase time_step_s or "
        "reduce duration_hours.",
    )

    _require(
        bc.internal_convection_w_m2k > 0, "internal_convection_w_m2k must be > 0"
    )
    _require(
        bc.external_convection_w_m2k > 0, "external_convection_w_m2k must be > 0"
    )

    # Physically-plausible temperature bounds (Earth-surface climates).
    for pt in bc.ambient_series:
        _require(
            -90.0 <= pt.ambient_temp_c <= 60.0,
            f"ambient_temp_c={pt.ambient_temp_c} at hour={pt.hour} is outside "
            "the plausible range [-90, 60] deg C",
        )
        _require(
            pt.solar_irradiance_w_m2 >= 0.0,
            f"solar_irradiance_w_m2 at hour={pt.hour} must be >= 0",
        )
        _require(
            pt.solar_irradiance_w_m2 <= 1500.0,
            f"solar_irradiance_w_m2={pt.solar_irradiance_w_m2} at hour={pt.hour} "
            "exceeds plausible peak terrestrial irradiance of ~1500 W/m^2",
        )

    _require(
        -90.0 <= bc.indoor_initial_temp_c <= 60.0,
        "indoor_initial_temp_c is outside the plausible range [-90, 60] deg C",
    )
    _require(
        -50.0 <= bc.ground_temp_c <= 40.0,
        "ground_temp_c is outside the plausible range [-50, 40] deg C",
    )


def validate_simulation_config(config) -> List[str]:
    """Validate a full SimulationConfig. Returns an empty list if
    valid; raises ValidationError on the first problem found (fail
    fast, since simulation setup depends on all pieces being sane).
    """
    validate_geometry(config.geometry)
    validate_material_assignment(config.materials)
    validate_boundary_conditions(config.boundary_conditions)
    return []
