"""Tests for thermal_engine.physics."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from thermal_engine.physics import (
    conduction_heat_flow,
    solar_heat_gain,
    temperature_change,
    u_value_single_layer,
)


def test_u_value_single_layer():
    assert u_value_single_layer(thermal_conductivity=1.0, thickness=0.5) == pytest.approx(2.0)
    assert u_value_single_layer(thermal_conductivity=0.04, thickness=0.1) == pytest.approx(0.4)


def test_conduction_heat_flow_indoor_warmer_is_positive_loss():
    # Indoor warmer than outdoor -> heat flows OUT -> positive Q.
    q = conduction_heat_flow(u_value=2.0, area=10.0, indoor_temp=20.0, outdoor_temp=0.0)
    assert q == pytest.approx(2.0 * 10.0 * 20.0)
    assert q > 0


def test_conduction_heat_flow_outdoor_warmer_is_negative_loss():
    # Outdoor warmer than indoor -> heat flows IN -> negative "loss" (a gain).
    q = conduction_heat_flow(u_value=2.0, area=10.0, indoor_temp=0.0, outdoor_temp=20.0)
    assert q == pytest.approx(-400.0)
    assert q < 0


def test_conduction_heat_flow_zero_delta_t():
    q = conduction_heat_flow(u_value=3.0, area=5.0, indoor_temp=10.0, outdoor_temp=10.0)
    assert q == pytest.approx(0.0)


def test_solar_heat_gain_basic():
    q = solar_heat_gain(solar_radiation=500.0, effective_area=20.0, solar_absorptivity=0.6)
    assert q == pytest.approx(500.0 * 20.0 * 0.6)
    assert q >= 0


def test_solar_heat_gain_zero_radiation_is_zero_gain():
    q = solar_heat_gain(solar_radiation=0.0, effective_area=20.0, solar_absorptivity=0.6)
    assert q == pytest.approx(0.0)


def test_solar_heat_gain_rejects_out_of_range_absorptivity():
    with pytest.raises(ValueError):
        solar_heat_gain(solar_radiation=500.0, effective_area=20.0, solar_absorptivity=1.5)


def test_solar_heat_gain_rejects_negative_radiation():
    with pytest.raises(ValueError):
        solar_heat_gain(solar_radiation=-10.0, effective_area=20.0, solar_absorptivity=0.5)


def test_temperature_change_positive_net_flow_warms():
    dT = temperature_change(net_heat_flow=1000.0, thermal_capacity=500000.0, timestep_seconds=3600.0)
    assert dT == pytest.approx(1000.0 * 3600.0 / 500000.0)
    assert dT > 0


def test_temperature_change_negative_net_flow_cools():
    dT = temperature_change(net_heat_flow=-1000.0, thermal_capacity=500000.0, timestep_seconds=3600.0)
    assert dT < 0


def test_temperature_change_rejects_non_positive_capacity():
    with pytest.raises(ValueError):
        temperature_change(net_heat_flow=100.0, thermal_capacity=0.0, timestep_seconds=3600.0)


def test_temperature_change_rejects_non_positive_timestep():
    with pytest.raises(ValueError):
        temperature_change(net_heat_flow=100.0, thermal_capacity=1000.0, timestep_seconds=0.0)
