"""
Material model.

A Material represents a single homogeneous layer used in a wall, roof,
or floor assembly (or a window/opening, if the user chooses to model
glazing as a material layer).

Units (SI, used consistently throughout the project):
    thermal_conductivity : W / (m * K)
    density              : kg / m^3
    specific_heat         : J / (kg * K)
    thickness            : m
    solar_absorptivity   : dimensionless, 0-1
    emissivity           : dimensionless, 0-1 (not used in the simplified
                            radiative model yet, but exposed for future
                            long-wave radiation extensions)
"""
from __future__ import annotations

from typing import List, Union

from pydantic import BaseModel, Field, field_validator


class Material(BaseModel):
    """A single homogeneous material layer."""

    name: str = Field(..., description="Human readable material name")
    thermal_conductivity: float = Field(
        ..., gt=0, description="Thermal conductivity k, W/(m*K)"
    )
    density: float = Field(..., gt=0, description="Density, kg/m^3")
    specific_heat: float = Field(
        ..., gt=0, description="Specific heat capacity c, J/(kg*K)"
    )
    thickness: float = Field(..., gt=0, description="Layer thickness, m")
    solar_absorptivity: float = Field(
        0.6, ge=0, le=1, description="Fraction of incident solar radiation absorbed"
    )
    emissivity: float = Field(
        0.9, ge=0, le=1, description="Long-wave emissivity (reserved for future use)"
    )

    @property
    def r_value(self) -> float:
        """Thermal resistance of this single layer, (m^2*K)/W."""
        return self.thickness / self.thermal_conductivity

    @property
    def u_value(self) -> float:
        """Thermal transmittance of this single layer, W/(m^2*K)."""
        return 1.0 / self.r_value

    @property
    def areal_heat_capacity(self) -> float:
        """Heat capacity per unit area of this layer, J/(m^2*K)."""
        return self.density * self.specific_heat * self.thickness


# A wall/roof/floor assembly can be a single Material or an ordered list of
# Material layers (e.g. brick + insulation + plaster). This lets the API
# support layered construction "where practical" without forcing every
# caller to wrap a single material in a list.
MaterialAssembly = Union[Material, List[Material]]


def as_layers(assembly: MaterialAssembly) -> List[Material]:
    """Normalize a MaterialAssembly into a list of layers."""
    if isinstance(assembly, list):
        return assembly
    return [assembly]


def assembly_r_value(assembly: MaterialAssembly) -> float:
    """Total thermal resistance of an assembly (layers in series)."""
    return sum(layer.r_value for layer in as_layers(assembly))


def assembly_u_value(assembly: MaterialAssembly) -> float:
    """Overall U-value of an assembly, U = 1 / sum(R_layers)."""
    r_total = assembly_r_value(assembly)
    return 1.0 / r_total


def assembly_areal_heat_capacity(assembly: MaterialAssembly) -> float:
    """Total heat capacity per unit area of an assembly, J/(m^2*K)."""
    return sum(layer.areal_heat_capacity for layer in as_layers(assembly))


def assembly_solar_absorptivity(assembly: MaterialAssembly) -> float:
    """
    Effective solar absorptivity of an assembly.

    Simplification: only the outermost (first-listed) layer is exposed to
    solar radiation, so its absorptivity governs the absorbed fraction.
    """
    layers = as_layers(assembly)
    return layers[0].solar_absorptivity
