"""
ShelterDesign: the candidate solution representation used throughout
the optimizer (genome -> phenotype).
"""

from dataclasses import dataclass, field
from typing import List


DEFAULT_CONSTRAINTS = {
    "length_min": 3.0, "length_max": 10.0,
    "width_min": 3.0, "width_max": 10.0,
    "height_min": 2.2, "height_max": 4.0,
    "wall_thickness_min": 0.10, "wall_thickness_max": 0.60,
    "roof_thickness_min": 0.10, "roof_thickness_max": 0.60,
    "floor_thickness_min": 0.05, "floor_thickness_max": 0.40,
    "insulation_thickness_min": 0.02, "insulation_thickness_max": 0.20,
    "opening_pct_min": 0.02, "opening_pct_max": 0.30,   # fraction of floor area
    "door_area_min": 1.6, "door_area_max": 2.4,
    "orientation_min": 0.0, "orientation_max": 359.0,
    "max_aspect_ratio": 2.5,          # length/width upper bound
    "max_material_cost_index": 400.0,  # optional cost ceiling (relative units)
}


@dataclass
class ShelterDesign:
    length: float
    width: float
    height: float
    wall_thickness: float
    roof_thickness: float
    floor_thickness: float
    insulation_thickness: float
    wall_material: str
    roof_material: str
    floor_material: str
    insulation_material: str
    opening_area: float   # m^2, total glazed/window area
    door_area: float       # m^2
    orientation: float      # degrees; 0 = openings face the equator (best winter sun)

    def floor_area(self) -> float:
        return self.length * self.width

    def gross_wall_area(self) -> float:
        return 2.0 * (self.length + self.width) * self.height

    def net_wall_area(self) -> float:
        return max(self.gross_wall_area() - self.opening_area - self.door_area, 0.0)

    def volume(self) -> float:
        return self.length * self.width * self.height

    def aspect_ratio(self) -> float:
        return max(self.length, self.width) / max(min(self.length, self.width), 1e-6)

    def validate(self, constraints: dict = None) -> List[str]:
        """Return a list of human-readable constraint violations (empty = valid)."""
        c = constraints or DEFAULT_CONSTRAINTS
        errors = []

        def check(val, lo_key, hi_key, label):
            if lo_key in c and val < c[lo_key]:
                errors.append(f"{label} {val:.3f} below minimum {c[lo_key]}")
            if hi_key in c and val > c[hi_key]:
                errors.append(f"{label} {val:.3f} above maximum {c[hi_key]}")

        check(self.length, "length_min", "length_max", "length")
        check(self.width, "width_min", "width_max", "width")
        check(self.height, "height_min", "height_max", "height")
        check(self.wall_thickness, "wall_thickness_min", "wall_thickness_max", "wall_thickness")
        check(self.roof_thickness, "roof_thickness_min", "roof_thickness_max", "roof_thickness")
        check(self.floor_thickness, "floor_thickness_min", "floor_thickness_max", "floor_thickness")
        check(self.insulation_thickness, "insulation_thickness_min",
              "insulation_thickness_max", "insulation_thickness")
        check(self.door_area, "door_area_min", "door_area_max", "door_area")

        if self.opening_area < 0:
            errors.append("opening_area cannot be negative")
        max_opening = c.get("opening_pct_max", 0.30) * self.floor_area()
        min_opening = c.get("opening_pct_min", 0.02) * self.floor_area()
        if self.opening_area > max_opening:
            errors.append(f"opening_area {self.opening_area:.2f} exceeds max allowed {max_opening:.2f}")
        if self.opening_area < min_opening:
            errors.append(f"opening_area {self.opening_area:.2f} below min required {min_opening:.2f}")

        if self.aspect_ratio() > c.get("max_aspect_ratio", 2.5):
            errors.append(f"aspect_ratio {self.aspect_ratio():.2f} exceeds max "
                           f"{c.get('max_aspect_ratio', 2.5)}")

        if not (c.get("orientation_min", 0) <= self.orientation <= c.get("orientation_max", 359)):
            errors.append(f"orientation {self.orientation} outside allowed range")

        return errors

    def is_valid(self, constraints: dict = None) -> bool:
        return len(self.validate(constraints)) == 0

    def summary_dict(self) -> dict:
        return {
            "length_m": round(self.length, 2),
            "width_m": round(self.width, 2),
            "height_m": round(self.height, 2),
            "wall_thickness_m": round(self.wall_thickness, 3),
            "roof_thickness_m": round(self.roof_thickness, 3),
            "floor_thickness_m": round(self.floor_thickness, 3),
            "insulation_thickness_m": round(self.insulation_thickness, 3),
            "wall_material": self.wall_material,
            "roof_material": self.roof_material,
            "floor_material": self.floor_material,
            "insulation_material": self.insulation_material,
            "opening_area_m2": round(self.opening_area, 2),
            "door_area_m2": round(self.door_area, 2),
            "orientation_deg": round(self.orientation, 1),
        }
