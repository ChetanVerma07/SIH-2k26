"""Location model: supports name-based or coordinate-based input."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Location:
    """A geographic location.

    Either `name` or (`latitude`, `longitude`) must be provided.
    Coordinates are in decimal degrees (WGS84). Latitude in [-90, 90],
    longitude in [-180, 180].
    """
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    elevation_m: Optional[float] = None  # meters above sea level

    def __post_init__(self):
        if self.name is None and (self.latitude is None or self.longitude is None):
            raise ValueError(
                "Location requires either a `name` or both `latitude` and `longitude`."
            )
        if self.latitude is not None and not (-90.0 <= self.latitude <= 90.0):
            raise ValueError(f"Invalid latitude: {self.latitude}. Must be in [-90, 90].")
        if self.longitude is not None and not (-180.0 <= self.longitude <= 180.0):
            raise ValueError(f"Invalid longitude: {self.longitude}. Must be in [-180, 180].")

    def has_coordinates(self) -> bool:
        return self.latitude is not None and self.longitude is not None

    def display_name(self) -> str:
        if self.name:
            return self.name
        return f"({self.latitude:.4f}, {self.longitude:.4f})"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "elevation_m": self.elevation_m,
        }
