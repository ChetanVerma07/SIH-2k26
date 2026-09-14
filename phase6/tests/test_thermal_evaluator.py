import sys, os, copy
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from optimizer.models.design import ShelterDesign
from optimizer.models.climate import SCENARIOS
from optimizer.thermal.simplified_model import FastThermalEvaluator


def base_design():
    return ShelterDesign(
        length=6.0, width=5.0, height=2.8,
        wall_thickness=0.25, roof_thickness=0.20, floor_thickness=0.15,
        insulation_thickness=0.08,
        wall_material="rammed_earth", roof_material="timber_frame",
        floor_material="stone_masonry", insulation_material="mineral_wool",
        opening_area=3.0, door_area=2.0, orientation=0.0,
    )


def test_evaluator_returns_required_keys():
    evaluator = FastThermalEvaluator()
    result = evaluator.evaluate(base_design(), SCENARIOS["cold_winter_day"])
    required = {
        "avg_indoor_temp_c", "min_indoor_temp_c", "max_indoor_temp_c",
        "comfort_percentage", "total_heat_loss_kwh", "total_solar_gain_kwh",
        "heating_requirement_kwh", "hourly_indoor_temp",
    }
    assert required.issubset(result.keys())
    assert len(result["hourly_indoor_temp"]) == 24


def test_more_insulation_reduces_heat_loss():
    evaluator = FastThermalEvaluator()
    climate = SCENARIOS["cold_winter_day"]

    thin = base_design()
    thin.insulation_thickness = 0.02
    thick = base_design()
    thick.insulation_thickness = 0.20

    r_thin = evaluator.evaluate(thin, climate)
    r_thick = evaluator.evaluate(thick, climate)

    assert r_thick["total_heat_loss_kwh"] < r_thin["total_heat_loss_kwh"]
    assert r_thick["heating_requirement_kwh"] < r_thin["heating_requirement_kwh"]


def test_more_opening_area_increases_heat_loss():
    evaluator = FastThermalEvaluator()
    climate = SCENARIOS["cold_cloudy_day"]  # low solar -> opening mostly adds loss

    small = base_design()
    small.opening_area = 1.0
    large = base_design()
    large.opening_area = 6.0

    r_small = evaluator.evaluate(small, climate)
    r_large = evaluator.evaluate(large, climate)

    assert r_large["total_heat_loss_kwh"] > r_small["total_heat_loss_kwh"]


def test_orientation_affects_solar_gain():
    evaluator = FastThermalEvaluator()
    climate = SCENARIOS["cold_sunny_day"]

    facing = base_design()
    facing.orientation = 0.0
    away = base_design()
    away.orientation = 180.0

    r_facing = evaluator.evaluate(facing, climate)
    r_away = evaluator.evaluate(away, climate)

    assert r_facing["total_solar_gain_kwh"] > r_away["total_solar_gain_kwh"]


def test_higher_conductivity_wall_material_increases_heat_loss():
    evaluator = FastThermalEvaluator()
    climate = SCENARIOS["cold_winter_day"]

    low_k = base_design()
    low_k.wall_material = "timber_frame"      # conductivity 0.13
    high_k = base_design()
    high_k.wall_material = "concrete_block"    # conductivity 1.35

    r_low = evaluator.evaluate(low_k, climate)
    r_high = evaluator.evaluate(high_k, climate)

    assert r_high["total_heat_loss_kwh"] > r_low["total_heat_loss_kwh"]


def test_evaluator_is_deterministic():
    evaluator = FastThermalEvaluator()
    design = base_design()
    climate = SCENARIOS["cold_winter_day"]
    r1 = evaluator.evaluate(design, climate)
    r2 = evaluator.evaluate(copy.deepcopy(design), climate)
    assert r1["total_heat_loss_kwh"] == r2["total_heat_loss_kwh"]
    assert r1["comfort_percentage"] == r2["comfort_percentage"]
