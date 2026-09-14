"""Simulation result, comparison, robustness and confidence models."""
from typing import Optional
from pydantic import BaseModel, Field


class ThermalPerformance(BaseModel):
    """Output of the thermal simulator for one design under one climate/scenario."""

    design_id: str
    avg_indoor_temp_c: float
    min_indoor_temp_c: float
    max_indoor_temp_c: float
    comfort_percentage: float = Field(ge=0, le=100)
    total_heat_loss_kwh: float = Field(ge=0)
    solar_gain_kwh: float = Field(ge=0)
    net_thermal_energy_kwh: float = Field(
        description="solar_gain_kwh minus total_heat_loss_kwh; negative means net loss"
    )
    estimated_heating_requirement_kwh: float = Field(
        ge=0, description="Auxiliary heating energy estimated to hold the comfort range"
    )
    material_cost_factor: float = Field(ge=0)
    overall_score: float = Field(description="Weighted composite score, higher is better")


class ScenarioResult(BaseModel):
    """Thermal performance of the recommended design under one alternate scenario."""

    scenario_name: str
    description: str
    min_indoor_temp_c: float
    max_indoor_temp_c: float
    avg_indoor_temp_c: float
    comfort_percentage: float
    heat_loss_kwh: float
    solar_gain_kwh: float


class RobustnessSummary(BaseModel):
    scenarios: list[ScenarioResult]
    scenarios_evaluated: int
    scenarios_passed: int = Field(description="Scenarios where comfort_percentage >= 60")
    worst_case_comfort_percentage: float
    average_comfort_percentage: float
    robustness_score: float = Field(ge=0, le=100)


class BaselineComparison(BaseModel):
    baseline_heat_loss_kwh: float
    optimized_heat_loss_kwh: float
    heat_loss_improvement_percent: float
    baseline_comfort_percentage: float
    optimized_comfort_percentage: float
    comfort_improvement_points: float
    baseline_heating_requirement_kwh: float
    optimized_heating_requirement_kwh: float
    heating_requirement_improvement_percent: float


class ConfidenceAssessment(BaseModel):
    data_confidence: float = Field(ge=0, le=100)
    simulation_confidence: float = Field(ge=0, le=100)
    recommendation_confidence: float = Field(ge=0, le=100)
    explanation: str


class ANSYSValidationResult(BaseModel):
    is_mock: bool = Field(default=True)
    design_id: str
    validated: bool
    predicted_max_stress_mpa: Optional[float] = None
    predicted_thermal_bridging_risk: str = Field(
        default="unknown", description="low, medium, or high (mock heuristic only)"
    )
    notes: str


class RecommendationExplanation(BaseModel):
    headline: str
    reasons: list[str]
    tradeoffs: list[str]


class WhatIfResult(BaseModel):
    parameter: str
    original_value: float | str
    new_value: float | str
    heat_loss_change_kwh: float
    comfort_change_points: float
    solar_gain_change_kwh: float
    score_change: float
    narrative: str
