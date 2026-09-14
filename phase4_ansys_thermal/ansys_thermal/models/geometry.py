"""
Geometry model for a passive shelter.

The base implementation supports a single, simple shape: a rectangular
(box-type) shelter. The dataclass is intentionally generic (a
``shape`` discriminator field) so that additional shapes (e.g. dome,
vault, L-shaped) can be added later without breaking the public API.

This module has NO dependency on ANSYS. It only describes geometry in
plain Python / JSON-serializable terms. Translation into an actual
ANSYS model happens in ``ansys_thermal.ansys.input_generator``.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, Any


class Orientation(float, Enum):
    """Common cardinal orientations, expressed as degrees from North.

    Any float value is accepted by ShelterGeometry; this enum is just a
    convenience for the common cases.
    """

    NORTH = 0.0
    EAST = 90.0
    SOUTH = 180.0
    WEST = 270.0


class ShelterShape(str, Enum):
    """Supported shelter shapes. Only RECTANGULAR is implemented in
    Phase 4. The field exists so future phases can extend geometry
    support without changing the surrounding architecture."""

    RECTANGULAR = "rectangular"
    # Placeholders for future extension (NOT implemented in Phase 4):
    # DOME = "dome"
    # VAULT = "vault"
    # L_SHAPED = "l_shaped"


@dataclass
class ShelterGeometry:
    """Parameterized geometry of a rectangular passive shelter.

    All linear dimensions are in metres, all areas in square metres,
    unless otherwise noted. Orientation is degrees measured clockwise
    from North (0 = North-facing front wall).
    """

    length: float
    width: float
    height: float

    wall_thickness: float
    roof_thickness: float
    floor_thickness: float

    window_area: float = 0.0
    door_area: float = 0.0
    other_openings_area: float = 0.0

    orientation_deg: float = 0.0

    shape: ShelterShape = ShelterShape.RECTANGULAR

    # ---- derived geometric quantities -------------------------------

    def floor_area(self) -> float:
        return self.length * self.width

    def roof_area(self) -> float:
        # Flat-roof assumption for the base rectangular model.
        return self.length * self.width

    def wall_gross_area(self) -> float:
        """Total gross external wall area (all four walls), before
        subtracting openings."""
        return 2.0 * (self.length + self.width) * self.height

    def total_opening_area(self) -> float:
        return self.window_area + self.door_area + self.other_openings_area

    def wall_net_area(self) -> float:
        """Wall area available for conduction, i.e. gross wall area
        minus all openings. Openings are assumed to be located on the
        walls (not the roof)."""
        net = self.wall_gross_area() - self.total_opening_area()
        return max(net, 0.0)

    def internal_volume(self) -> float:
        """Approximate internal air volume, ignoring wall thickness."""
        return self.length * self.width * self.height

    def as_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["shape"] = self.shape.value if isinstance(self.shape, ShelterShape) else self.shape
        d["derived"] = {
            "floor_area_m2": round(self.floor_area(), 4),
            "roof_area_m2": round(self.roof_area(), 4),
            "wall_gross_area_m2": round(self.wall_gross_area(), 4),
            "wall_net_area_m2": round(self.wall_net_area(), 4),
            "total_opening_area_m2": round(self.total_opening_area(), 4),
            "internal_volume_m3": round(self.internal_volume(), 4),
        }
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ShelterGeometry":
        data = dict(data)
        data.pop("derived", None)
        shape = data.pop("shape", ShelterShape.RECTANGULAR.value)
        geom = cls(shape=ShelterShape(shape), **data)
        return geom
