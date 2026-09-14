"""
Steady-state conduction relationships.

Core equation (Fourier's law applied across a plane layer):

    Q = U * A * dT

where:
    Q  = heat flow, W
    U  = overall thermal transmittance, W/(m^2*K)
    A  = area, m^2
    dT = temperature difference across the element, K (or degC, equivalent)

U is derived from thermal resistance R:

    R = thickness / thermal_conductivity      (single layer, (m^2*K)/W)
    R_total = sum(R_layers)                   (layers in series)
    U = 1 / R_total

This module only implements the pure physics; it does not know about
shelters or climates.
"""
from __future__ import annotations

from app.models.material import MaterialAssembly, assembly_u_value


def conductive_heat_flow(u_value: float, area: float, delta_t: float) -> float:
    """
    Q = U * A * dT

    Positive delta_t (indoor - outdoor) with positive u_value/area yields a
    positive heat loss (heat flowing outward from the warmer indoor space).
    """
    return u_value * area * delta_t


def assembly_conductive_loss(assembly: MaterialAssembly, area: float, delta_t: float) -> float:
    """Convenience wrapper: compute U from a material assembly, then Q=U*A*dT."""
    u = assembly_u_value(assembly)
    return conductive_heat_flow(u, area, delta_t)
