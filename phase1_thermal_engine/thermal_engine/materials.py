"""
materials.py
============

Reusable material model for the thermal engine.

A ``Material`` represents a single homogeneous building-material layer
(e.g. a wall's concrete leaf, a roof's insulation board) with the physical
properties needed for a lumped-parameter conduction + thermal-mass model:

- thermal_conductivity (k)  [W/(m.K)]   -> governs conduction / U-value
- density (rho)             [kg/m^3]    -> governs thermal mass
- specific_heat (c)         [J/(kg.K)]  -> governs thermal mass
- thickness (t)             [m]         -> governs U-value and mass
- solar_absorptivity        [0-1]       -> governs solar heat gain
- emissivity                [0-1]       -> radiative property, carried for
                                            completeness / future long-wave
                                            radiation modelling (not used in
                                            the Phase 1 physics yet)

The module intentionally does NOT hard-code the rest of the engine around
any specific material: ``Material`` instances are plain, user-constructible
objects, and :data:`EXAMPLE_MATERIALS` is just a convenience dictionary of
illustrative values for demos and tests.
"""

from __future__ import annotations

from dataclasses import dataclass

from .validation import (
    validate_fraction,
    validate_non_empty_string,
    validate_positive,
)


@dataclass(frozen=True)
class Material:
    """
    A single homogeneous material layer used for walls, roofs or floors.

    Attributes:
        name: Human-readable material name (e.g. "Fired Clay Brick").
        thermal_conductivity: Thermal conductivity k, in W/(m.K). Must be > 0.
        density: Material density, in kg/m^3. Must be > 0.
        specific_heat: Specific heat capacity, in J/(kg.K). Must be > 0.
        thickness: Layer thickness, in m. Must be > 0.
        solar_absorptivity: Fraction of incident solar radiation absorbed
            by the outer surface, dimensionless in [0, 1].
        emissivity: Long-wave emissivity of the outer surface, dimensionless
            in [0, 1]. Reserved for future radiative-loss modelling.

    Raises:
        ThermalEngineValidationError: if any property is physically invalid
            (e.g. non-positive thickness, absorptivity outside [0, 1]).
    """

    name: str
    thermal_conductivity: float
    density: float
    specific_heat: float
    thickness: float
    solar_absorptivity: float
    emissivity: float = 0.9

    def __post_init__(self) -> None:
        # dataclass is frozen, but we can still validate in __post_init__;
        # object.__setattr__ is only needed if we wanted to coerce values.
        validate_non_empty_string(self.name, "name")
        validate_positive(self.thermal_conductivity, "thermal_conductivity")
        validate_positive(self.density, "density")
        validate_positive(self.specific_heat, "specific_heat")
        validate_positive(self.thickness, "thickness")
        validate_fraction(self.solar_absorptivity, "solar_absorptivity")
        validate_fraction(self.emissivity, "emissivity")

    @property
    def u_value(self) -> float:
        """
        Conductive U-value of this single layer, in W/(m^2.K).

        Computed as k / thickness (pure conduction resistance only; surface
        air-film resistances are neglected in this simplified Phase 1
        model -- see README "Assumptions").
        """
        return self.thermal_conductivity / self.thickness

    @property
    def thermal_resistance(self) -> float:
        """Conductive resistance R = thickness / k, in m^2.K/W."""
        return self.thickness / self.thermal_conductivity

    def mass_per_unit_area(self) -> float:
        """Mass of this layer per unit surface area, in kg/m^2."""
        return self.density * self.thickness

    def heat_capacity_per_unit_area(self) -> float:
        """
        Areal heat capacity of this layer, in J/(m^2.K).

        This is mass-per-area * specific heat, and is used to build up the
        shelter's total thermal mass from its wall/roof/floor materials.
        """
        return self.mass_per_unit_area() * self.specific_heat


# ---------------------------------------------------------------------------
# Example materials for demonstration and testing.
#
# Values are representative, commonly-cited approximations for these
# material classes (typical ranges found in building-physics references),
# NOT measured data for any specific product. They are intended to produce
# realistic-looking demo behaviour, not to be used for real construction
# decisions.
# ---------------------------------------------------------------------------

EXAMPLE_MATERIALS: dict[str, Material] = {
    "mud_adobe": Material(
        name="Mud Adobe (traditional, 300mm)",
        thermal_conductivity=0.50,
        density=1600.0,
        specific_heat=900.0,
        thickness=0.30,
        solar_absorptivity=0.70,
        emissivity=0.90,
    ),
    "rammed_earth": Material(
        name="Rammed Earth (450mm)",
        thermal_conductivity=0.55,
        density=1900.0,
        specific_heat=850.0,
        thickness=0.45,
        solar_absorptivity=0.65,
        emissivity=0.90,
    ),
    "fired_brick": Material(
        name="Fired Clay Brick (230mm)",
        thermal_conductivity=0.72,
        density=1700.0,
        specific_heat=840.0,
        thickness=0.23,
        solar_absorptivity=0.60,
        emissivity=0.90,
    ),
    "concrete": Material(
        name="Cast Concrete (150mm)",
        thermal_conductivity=1.40,
        density=2300.0,
        specific_heat=880.0,
        thickness=0.15,
        solar_absorptivity=0.65,
        emissivity=0.90,
    ),
    "rock_wool_insulation": Material(
        name="Rock Wool Insulation Board (100mm)",
        thermal_conductivity=0.040,
        density=100.0,
        specific_heat=840.0,
        thickness=0.10,
        solar_absorptivity=0.50,
        emissivity=0.90,
    ),
    "eps_insulation": Material(
        name="Expanded Polystyrene (80mm)",
        thermal_conductivity=0.035,
        density=20.0,
        specific_heat=1450.0,
        thickness=0.08,
        solar_absorptivity=0.45,
        emissivity=0.90,
    ),
    "timber_plank": Material(
        name="Timber Plank (40mm)",
        thermal_conductivity=0.14,
        density=550.0,
        specific_heat=1600.0,
        thickness=0.04,
        solar_absorptivity=0.55,
        emissivity=0.90,
    ),
    "cgi_sheet_roof": Material(
        name="Corrugated Galvanised Iron Sheet (0.6mm)",
        thermal_conductivity=50.0,
        density=7850.0,
        specific_heat=450.0,
        thickness=0.0006,
        solar_absorptivity=0.55,
        emissivity=0.28,
    ),
    "straw_bale": Material(
        name="Straw Bale (450mm)",
        thermal_conductivity=0.07,
        density=110.0,
        specific_heat=2000.0,
        thickness=0.45,
        solar_absorptivity=0.60,
        emissivity=0.90,
    ),
}
