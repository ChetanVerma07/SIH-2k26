"""
Shelter builder.

Translates a ``ShelterGeometry`` (plain engineering parameters) into a
structured, element-based description that maps cleanly onto how an
ANSYS thermal model would be built: a set of named surfaces/solids,
each with an area, thickness, and orientation tag.

This module does NOT talk to ANSYS. It produces a
JSON-serializable "build plan" that the ANSYS input generator
(``ansys_thermal.ansys.input_generator``) consumes to write ANSYS
Mechanical APDL (.dat) / Workbench-journal-style input files.

Only a rectangular shelter is implemented in Phase 4 (per the base
requirement). The ``ShelterElement`` list-based design means future
shapes can be supported by adding a new builder function that returns
the same element structure.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Dict, Any

from ansys_thermal.models.geometry import ShelterGeometry, ShelterShape


@dataclass
class ShelterElement:
    """One planar building element (wall, roof, floor, or opening
    group) with the data needed to build/mesh it in ANSYS."""

    element_id: str
    element_type: str  # "wall" | "roof" | "floor" | "opening"
    area_m2: float
    thickness_m: float
    orientation_deg: float  # 0=N, 90=E, 180=S, 270=W; roof/floor = -1
    exposed_to_ambient: bool
    exposed_to_solar: bool

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ShelterBuildPlan:
    """The full set of elements describing one shelter, plus overall
    metadata needed downstream (e.g. internal volume for lumped-air
    thermal mass)."""

    shape: str
    elements: List[ShelterElement]
    internal_volume_m3: float
    orientation_deg: float

    def as_dict(self) -> Dict[str, Any]:
        return {
            "shape": self.shape,
            "orientation_deg": self.orientation_deg,
            "internal_volume_m3": self.internal_volume_m3,
            "elements": [e.as_dict() for e in self.elements],
        }

    def total_area_by_type(self, element_type: str) -> float:
        return sum(e.area_m2 for e in self.elements if e.element_type == element_type)


def build_rectangular_shelter(geometry: ShelterGeometry) -> ShelterBuildPlan:
    """Build a ``ShelterBuildPlan`` for a rectangular shelter.

    Simplification (documented): the four walls are split evenly by
    perimeter fraction, and all openings (window + door + other) are
    lumped into a single "opening" element attributed to the
    orientation-facing (front) wall. This is sufficient for the
    lumped/1-D-per-surface thermal network used by the mock adapter,
    and is a reasonable starting point for an ANSYS model — a real
    ANSYS model can place openings on any wall as needed by editing
    the generated geometry description.
    """

    if geometry.shape != ShelterShape.RECTANGULAR:
        raise NotImplementedError(
            f"Shelter shape '{geometry.shape}' is not implemented in Phase 4. "
            "Only 'rectangular' is supported. Extend shelter_builder.py to add "
            "new shapes."
        )

    elements: List[ShelterElement] = []

    # Four walls: front (facing `orientation_deg`), right, back, left.
    wall_orientations = [
        geometry.orientation_deg % 360.0,
        (geometry.orientation_deg + 90.0) % 360.0,
        (geometry.orientation_deg + 180.0) % 360.0,
        (geometry.orientation_deg + 270.0) % 360.0,
    ]
    # Two walls have length `length`, two have length `width`
    # (front/back use `length`, left/right use `width`).
    wall_lengths = [geometry.length, geometry.width, geometry.length, geometry.width]

    opening_area_remaining = geometry.total_opening_area()

    for i, (orient, wlen) in enumerate(zip(wall_orientations, wall_lengths)):
        gross_area = wlen * geometry.height
        # Attribute openings to the front wall (index 0) first, capped
        # at that wall's gross area, to keep the model physically valid.
        opening_on_this_wall = 0.0
        if i == 0 and opening_area_remaining > 0:
            opening_on_this_wall = min(opening_area_remaining, gross_area * 0.9)
            opening_area_remaining -= opening_on_this_wall

        net_wall_area = max(gross_area - opening_on_this_wall, 0.0)

        elements.append(
            ShelterElement(
                element_id=f"wall_{i+1}",
                element_type="wall",
                area_m2=round(net_wall_area, 4),
                thickness_m=geometry.wall_thickness,
                orientation_deg=orient,
                exposed_to_ambient=True,
                exposed_to_solar=True,
            )
        )

        if opening_on_this_wall > 0:
            elements.append(
                ShelterElement(
                    element_id=f"opening_wall_{i+1}",
                    element_type="opening",
                    area_m2=round(opening_on_this_wall, 4),
                    thickness_m=0.02,  # typical glazing/door thickness placeholder
                    orientation_deg=orient,
                    exposed_to_ambient=True,
                    exposed_to_solar=True,
                )
            )

    # If openings exceed the front wall capacity, distribute remainder
    # across other walls (rare edge case, but handled explicitly
    # rather than silently dropped).
    wall_idx = 1
    while opening_area_remaining > 1e-6 and wall_idx < len(elements):
        el = elements[wall_idx]
        if el.element_type == "wall":
            transfer = min(opening_area_remaining, el.area_m2 * 0.5)
            el.area_m2 = round(el.area_m2 - transfer, 4)
            elements.append(
                ShelterElement(
                    element_id=f"opening_extra_{wall_idx}",
                    element_type="opening",
                    area_m2=round(transfer, 4),
                    thickness_m=0.02,
                    orientation_deg=el.orientation_deg,
                    exposed_to_ambient=True,
                    exposed_to_solar=True,
                )
            )
            opening_area_remaining -= transfer
        wall_idx += 1

    elements.append(
        ShelterElement(
            element_id="roof",
            element_type="roof",
            area_m2=round(geometry.roof_area(), 4),
            thickness_m=geometry.roof_thickness,
            orientation_deg=-1.0,
            exposed_to_ambient=True,
            exposed_to_solar=True,
        )
    )

    elements.append(
        ShelterElement(
            element_id="floor",
            element_type="floor",
            area_m2=round(geometry.floor_area(), 4),
            thickness_m=geometry.floor_thickness,
            orientation_deg=-1.0,
            exposed_to_ambient=False,  # assumed on-grade, exposed to ground temp instead
            exposed_to_solar=False,
        )
    )

    return ShelterBuildPlan(
        shape=geometry.shape.value,
        elements=elements,
        internal_volume_m3=round(geometry.internal_volume(), 4),
        orientation_deg=geometry.orientation_deg,
    )
