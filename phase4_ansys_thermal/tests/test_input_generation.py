import json
from pathlib import Path

from ansys_thermal.ansys import input_generator
from ansys_thermal.models.simulation import SimulationConfig


def test_generate_json_config(tmp_path, simple_config):
    out = input_generator.generate_json_config(simple_config, tmp_path / "config.json")
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["name"] == "test_shelter"
    assert "geometry" in data and "materials" in data and "boundary_conditions" in data


def test_json_config_round_trips_to_simulation_config(tmp_path, simple_config):
    out = input_generator.generate_json_config(simple_config, tmp_path / "config.json")
    data = json.loads(out.read_text())
    restored = SimulationConfig.from_dict(data)
    assert restored.name == simple_config.name
    assert restored.geometry.length == simple_config.geometry.length


def test_generate_human_summary(tmp_path, simple_config):
    out = input_generator.generate_human_summary(simple_config, tmp_path / "summary.txt")
    assert out.exists()
    text = out.read_text()
    assert "SIMULATION CONFIGURATION SUMMARY" in text
    assert simple_config.name in text


def test_generate_apdl_skeleton(tmp_path, simple_config):
    out = input_generator.generate_apdl_skeleton(simple_config, tmp_path / "model.dat")
    assert out.exists()
    text = out.read_text()
    assert "/PREP7" in text
    assert "ET,1,SOLID70" in text
    assert "ANTYPE,TRANS" in text
    # Must clearly document that this is a skeleton, not a validated model
    assert "skeleton" in text.lower()


def test_generate_all_inputs(tmp_path, simple_config):
    paths = input_generator.generate_all_inputs(simple_config, tmp_path)
    assert set(paths.keys()) == {"json_config", "human_summary", "apdl_skeleton"}
    for p in paths.values():
        assert p.exists()
