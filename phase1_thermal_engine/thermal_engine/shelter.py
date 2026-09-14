"""
shelter.py
==========

Shelter configuration model: simple rectangular-box geometry plus the
materials assigned to its walls, roof and floor, and its openings
(windows/doors).

Geometry assumptions (see README for full list):

- The shelter is modelled as a simple rectangular box: length x width x
  height, with a single flat roof and a single floor slab.
- Wall area is the total external wall area (all four walls) minus the
  total opening area.
- Opening area is treated as a single lumped value with its own U-value
  (typical of a simplified glazing/door assumption), rather than modelling
  each window individually.
- "Solar exposed area" defaults to the roof area plus a user-adjustable
  fraction of wall area that is assumed to receive direct sun; it can also
  be set explicitly for a specific site/orientation study.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .materials import Material
from .validation import (
    validate_fraction,
    validate_non_negative,
    validate_positive,
    validate_positive_int,
    validate_temperature_celsius,
)

#: Combined indoor + outdoor surface (convective air film) resistance,
#: in m^2.K/W, added in series with each material's conductive resistance
#: to get an overall surface U-value.
#:
#: Real surfaces are not pure conductors: a thin film of still-ish air
#: clings to both faces and adds real thermal resistance -- this is why,
#: for example, a bare steel sheet roof does not behave as a near-perfect
#: conductor in practice. Standard building-physics references (e.g. ISO
#: 6946) tabulate separate internal/external film resistances per surface
#: orientation and airflow condition (typically ~0.04-0.17 m^2.K/W each).
#: Phase 1 uses one representative combined value for every opaque
#: surface (walls, roof, floor) rather than a full orientation-specific
#: table -- see README "Assumptions". Without this term, a thin, highly
#: conductive material (e.g. sheet metal) produces an unrealistically
#: large U-value that is both physically wrong and numerically unstable
#: for an explicit time-stepping scheme.
SURFACE_FILM_RESISTANCE = 0.17  # m^2.K/W


@dataclass(frozen=True)
class Shelter:
    """
    A simple rectangular-box shelter configuration.

    Attributes:
        name: Human-readable design name (e.g. "Design A - Insulated Wall").
        length: External footprint length, in m. Must be > 0.
        width: External footprint width, in m. Must be > 0.
        height: Wall height, in m. Must be > 0.
        wall_material: Material used for all four walls.
        roof_material: Material used for the roof.
        floor_material: Material used for the floor slab.
        num_openings: Number of windows/doors. Must be a positive integer.
        opening_area_each: Area of a single opening, in m^2. Must be >= 0.
        opening_u_value: Lumped U-value of each opening (glazing/door),
            in W/(m^2.K). Must be > 0.
        initial_indoor_temperature: Starting indoor air temperature, C.
        solar_wall_fraction: Fraction (0-1) of total wall area assumed to
            be directly sun-exposed at any given time. Used only if
            ``solar_exposed_area_override`` is not provided.
        solar_exposed_area_override: If provided, overrides the
            automatically computed solar-exposed area (m^2). Useful for
            site/orientation-specific studies.
        comfort_range: Optional (min, max) indoor comfort band in Celsius,
            used to compute "time within comfort range" metrics.
    """

    name: str
    length: float
    width: float
    height: float
    wall_material: Material
    roof_material: Material
    floor_material: Material
    num_openings: int = 1
    opening_area_each: float = 1.0
    opening_u_value: float = 2.8
    initial_indoor_temperature: float = 15.0
    solar_wall_fraction: float = 0.25
    solar_exposed_area_override: float | None = None
    comfort_range: tuple[float, float] | None = field(default=None)

    def __post_init__(self) -> None:
        validate_positive(self.length, "length")
        validate_positive(self.width, "width")
        validate_positive(self.height, "height")
        validate_positive_int(self.num_openings, "num_openings")
        validate_non_negative(self.opening_area_each, "opening_area_each")
        validate_positive(self.opening_u_value, "opening_u_value")
        validate_temperature_celsius(
            self.initial_indoor_temperature, "initial_indoor_temperature"
        )
        validate_fraction(self.solar_wall_fraction, "solar_wall_fraction")
        if self.solar_exposed_area_override is not None:
            validate_non_negative(
                self.solar_exposed_area_override, "solar_exposed_area_override"
            )
        if not isinstance(self.wall_material, Material):
            raise TypeError("'wall_material' must be a Material instance.")
        if not isinstance(self.roof_material, Material):
            raise TypeError("'roof_material' must be a Material instance.")
        if not isinstance(self.floor_material, Material):
            raise TypeError("'floor_material' must be a Material instance.")

        total_opening_area = self.num_openings * self.opening_area_each
        gross_wall_area = 2 * (self.length + self.width) * self.height
        if total_opening_area > gross_wall_area:
            raise ValueError(
                f"Total opening area ({total_opening_area:.2f} m^2) cannot "
                f"exceed the gross wall area ({gross_wall_area:.2f} m^2)."
            )

    # -- Derived geometry -------------------------------------------------

    @property
    def floor_area(self) -> float:
        """Floor (and roof footprint) area, in m^2."""
        return self.length * self.width

    @property
    def roof_area(self) -> float:
        """Roof area, in m^2 (flat roof, equal to the footprint)."""
        return self.floor_area

    @property
    def gross_wall_area(self) -> float:
        """Total external wall area before subtracting openings, in m^2."""
        return 2 * (self.length + self.width) * self.height

    @property
    def total_opening_area(self) -> float:
        """Total window/door area, in m^2."""
        return self.num_openings * self.opening_area_each

    @property
    def net_wall_area(self) -> float:
        """Opaque wall area (gross wall area minus openings), in m^2."""
        return self.gross_wall_area - self.total_opening_area

    @property
    def volume(self) -> float:
        """Internal air volume, in m^3."""
        return self.length * self.width * self.height

    @property
    def solar_exposed_area(self) -> float:
        """
        Effective sun-exposed area used for the solar-gain calculation, m^2.

        Defaults to: roof_area + solar_wall_fraction * net_wall_area,
        unless ``solar_exposed_area_override`` was supplied.
        """
        if self.solar_exposed_area_override is not None:
            return self.solar_exposed_area_override
        return self.roof_area + self.solar_wall_fraction * self.net_wall_area

    # -- Derived thermal properties ---------------------------------------

    @property
    def wall_u_value(self) -> float:
        """
        Overall wall U-value, W/(m^2.K): material conduction in series
        with :data:`SURFACE_FILM_RESISTANCE` on both faces.
        """
        return 1.0 / (self.wall_material.thermal_resistance + SURFACE_FILM_RESISTANCE)

    @property
    def roof_u_value(self) -> float:
        """
        Overall roof U-value, W/(m^2.K): material conduction in series
        with :data:`SURFACE_FILM_RESISTANCE` on both faces.
        """
        return 1.0 / (self.roof_material.thermal_resistance + SURFACE_FILM_RESISTANCE)

    @property
    def floor_u_value(self) -> float:
        """
        Overall floor U-value, W/(m^2.K): material conduction in series
        with :data:`SURFACE_FILM_RESISTANCE` on both faces.
        """
        return 1.0 / (self.floor_material.thermal_resistance + SURFACE_FILM_RESISTANCE)

    @property
    def thermal_capacity(self) -> float:
        """
        Total effective thermal (heat) capacity of the shelter's building
        fabric, in J/K.

        Computed as the sum, over walls/roof/floor, of each material's
        areal heat capacity multiplied by its surface area. This is a
        simplification: it represents the structural thermal mass only.
        The (usually much smaller) heat capacity of the indoor air itself
        is neglected -- see README "Assumptions".
        """
        wall_mass_capacity = (
            self.wall_material.heat_capacity_per_unit_area() * self.net_wall_area
        )
        roof_mass_capacity = (
            self.roof_material.heat_capacity_per_unit_area() * self.roof_area
        )
        floor_mass_capacity = (
            self.floor_material.heat_capacity_per_unit_area() * self.floor_area
        )
        return wall_mass_capacity + roof_mass_capacity + floor_mass_capacity
