"""Deterministic mock design optimizer.

Generates a fixed, deterministic grid of candidate designs by varying
wall material, insulation thickness, orientation and opening area. A real
implementation could replace this with a genetic algorithm, Bayesian
optimizer, or generative-design ML model, without the orchestrator
changing at all.
"""
import itertools

from app.interfaces.optimizer import DesignOptimizer
from app.models.climate import ClimateProfile
from app.models.design import ShelterDesign, WallMaterial, RoofMaterial, FloorMaterial
from app.models.request import ShelterDesignRequest

_WALL_OPTIONS = [
    WallMaterial.RAMMED_EARTH,
    WallMaterial.STONE_INSULATED,
    WallMaterial.TIMBER_INSULATED,
]
_INSULATION_OPTIONS_M = [0.05, 0.15]
_ORIENTATION_OPTIONS_DEG = [180.0, 90.0]
_OPENING_AREA_OPTIONS_M2 = [2.0, 4.0]


class MockDesignOptimizer(DesignOptimizer):
    def generate_candidates(
        self, request: ShelterDesignRequest, climate: ClimateProfile
    ) -> list[ShelterDesign]:
        length_m, width_m, height_m = 6.0, 4.0, 2.7

        # Favor a more weather-resistant roof/floor in cold high-altitude
        # climates; otherwise use a simpler default. Deterministic keyword
        # match, not a learned rule.
        if "cold" in climate.climate_zone.lower():
            roof = RoofMaterial.INSULATED_METAL
            floor = FloorMaterial.INSULATED_CONCRETE
        else:
            roof = RoofMaterial.TIMBER_INSULATED
            floor = FloorMaterial.RAISED_TIMBER

        candidates: list[ShelterDesign] = []
        combos = itertools.product(
            _WALL_OPTIONS, _INSULATION_OPTIONS_M, _ORIENTATION_OPTIONS_DEG, _OPENING_AREA_OPTIONS_M2
        )
        for i, (wall, insulation, orientation, opening_area) in enumerate(combos, start=1):
            candidates.append(
                ShelterDesign(
                    design_id=f"candidate-{i:02d}",
                    label=f"Candidate {i}",
                    length_m=length_m,
                    width_m=width_m,
                    height_m=height_m,
                    orientation_deg=orientation,
                    wall_material=wall,
                    roof_material=roof,
                    floor_material=floor,
                    insulation_thickness_m=insulation,
                    opening_area_m2=opening_area,
                    is_baseline=False,
                )
            )
        return candidates

    def generate_baseline(
        self, request: ShelterDesignRequest, climate: ClimateProfile
    ) -> ShelterDesign:
        return ShelterDesign(
            design_id="baseline",
            label="Baseline (conventional)",
            length_m=6.0,
            width_m=4.0,
            height_m=2.7,
            orientation_deg=90.0,
            wall_material=WallMaterial.MUD_BRICK,
            roof_material=RoofMaterial.THATCH,
            floor_material=FloorMaterial.COMPACTED_EARTH,
            insulation_thickness_m=0.0,
            opening_area_m2=3.0,
            is_baseline=True,
        )
