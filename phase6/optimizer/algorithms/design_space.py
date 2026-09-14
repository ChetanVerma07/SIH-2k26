"""
Configurable design-space definition shared by every optimization
algorithm. A "genome" here is a flat dict of gene_name -> value. The
schema below controls how each gene is generated, mutated and decoded
into a ShelterDesign.

Edit DEFAULT_DESIGN_SPACE (or build your own and pass it in) to change
the search ranges — nothing about the algorithms needs to change.
"""

import random
from optimizer.models.design import ShelterDesign
from optimizer.models.materials import structural_materials, insulation_materials

STRUCTURAL_NAMES = [m.name for m in structural_materials()]
INSULATION_NAMES = [m.name for m in insulation_materials()]

DEFAULT_DESIGN_SPACE = {
    "length":               {"type": "float", "min": 3.0, "max": 10.0, "step": 0.5},
    "width":                {"type": "float", "min": 3.0, "max": 10.0, "step": 0.5},
    "height":               {"type": "float", "min": 2.2, "max": 4.0, "step": 0.1},
    "wall_thickness":       {"type": "float", "min": 0.10, "max": 0.50, "step": 0.02},
    "roof_thickness":       {"type": "float", "min": 0.10, "max": 0.50, "step": 0.02},
    "floor_thickness":      {"type": "float", "min": 0.05, "max": 0.30, "step": 0.02},
    "insulation_thickness": {"type": "float", "min": 0.02, "max": 0.20, "step": 0.01},
    "wall_material":        {"type": "categorical", "choices": STRUCTURAL_NAMES},
    "roof_material":        {"type": "categorical", "choices": STRUCTURAL_NAMES},
    "floor_material":       {"type": "categorical", "choices": STRUCTURAL_NAMES},
    "insulation_material":  {"type": "categorical", "choices": INSULATION_NAMES},
    "opening_pct":          {"type": "float", "min": 0.02, "max": 0.30, "step": 0.01},
    "door_area":            {"type": "float", "min": 1.6, "max": 2.4, "step": 0.1},
    "orientation":           {"type": "float", "min": 0.0, "max": 359.0, "step": 5.0},
}


def _snap(value, gene_def):
    step = gene_def.get("step")
    lo, hi = gene_def["min"], gene_def["max"]
    if step:
        n_steps = round((value - lo) / step)
        value = lo + n_steps * step
    return max(lo, min(hi, value))


def random_gene(name, gene_def, rng: random.Random):
    if gene_def["type"] == "float":
        return _snap(rng.uniform(gene_def["min"], gene_def["max"]), gene_def)
    elif gene_def["type"] == "categorical":
        return rng.choice(gene_def["choices"])
    raise ValueError(f"Unknown gene type for {name}")


def random_genome(design_space, rng: random.Random) -> dict:
    return {name: random_gene(name, gd, rng) for name, gd in design_space.items()}


def mutate_gene(name, value, gene_def, rng: random.Random, mutation_strength=0.15):
    if gene_def["type"] == "float":
        span = gene_def["max"] - gene_def["min"]
        delta = rng.gauss(0, mutation_strength * span)
        return _snap(value + delta, gene_def)
    elif gene_def["type"] == "categorical":
        if rng.random() < 0.5:
            return rng.choice(gene_def["choices"])
        return value
    raise ValueError(f"Unknown gene type for {name}")


def clamp_gene(name, value, gene_def):
    if gene_def["type"] == "float":
        return _snap(value, gene_def)
    return value


def genome_to_design(genome: dict) -> ShelterDesign:
    floor_area = genome["length"] * genome["width"]
    opening_area = genome["opening_pct"] * floor_area
    return ShelterDesign(
        length=genome["length"],
        width=genome["width"],
        height=genome["height"],
        wall_thickness=genome["wall_thickness"],
        roof_thickness=genome["roof_thickness"],
        floor_thickness=genome["floor_thickness"],
        insulation_thickness=genome["insulation_thickness"],
        wall_material=genome["wall_material"],
        roof_material=genome["roof_material"],
        floor_material=genome["floor_material"],
        insulation_material=genome["insulation_material"],
        opening_area=opening_area,
        door_area=genome["door_area"],
        orientation=genome["orientation"],
    )
