"""The orchestration and decision layer.

The Orchestrator depends only on the abstract interfaces
(ClimateProvider, ThermalSimulator, DesignOptimizer, ANSYSValidator) via
dependency injection. It never instantiates a concrete provider itself,
so swapping a mock for a real implementation requires no change here.
"""
from app.interfaces.ansys import ANSYSValidator
from app.interfaces.climate import ClimateProvider
from app.interfaces.optimizer import DesignOptimizer
from app.interfaces.thermal import ThermalSimulator
from app.models.report import EngineeringReport
from app.models.request import ShelterDesignRequest
from app.models.results import BaselineComparison, ThermalPerformance
from app.services.confidence import assess_confidence
from app.services.recommendation import generate_recommendation
from app.services.robustness import evaluate_robustness

ASSUMPTIONS = [
    "Thermal envelope is modeled as a lumped single-zone conductance (UA) network; "
    "no multi-zone or CFD airflow modeling is performed.",
    "Material thermal conductivities and U-values are illustrative approximations, "
    "not laboratory-measured or standards-certified values.",
    "Occupant internal heat gains, appliance loads, and infiltration/ventilation "
    "losses are not modeled.",
    "Solar gain uses a fixed solar heat gain coefficient (0.60) for all openings "
    "regardless of actual glazing specification.",
    "Climate data is derived from keyword matching on the climate description, "
    "not measured station or satellite data.",
]

LIMITATIONS = [
    "This is a MOCK simulation for orchestration-layer development. Results must "
    "not be used for real construction or engineering decisions.",
    "Final engineering deployment requires validated material properties.",
    "Final engineering deployment requires calibrated, location-specific climate inputs.",
    "Final engineering deployment requires ANSYS or other high-fidelity FEA/CFD simulation.",
    "Final engineering deployment requires experimental validation where appropriate.",
    "Final engineering deployment requires domain-expert (structural/thermal engineer) review.",
]


class Orchestrator:
    def __init__(
        self,
        climate_provider: ClimateProvider,
        thermal_simulator: ThermalSimulator,
        optimizer: DesignOptimizer,
        ansys_validator: ANSYSValidator,
    ) -> None:
        self._climate_provider = climate_provider
        self._thermal_simulator = thermal_simulator
        self._optimizer = optimizer
        self._ansys_validator = ansys_validator

    @staticmethod
    def _compare(baseline: ThermalPerformance, optimized: ThermalPerformance) -> BaselineComparison:
        def pct_improvement(base: float, opt: float) -> float:
            if base == 0:
                return 0.0
            return round((base - opt) / base * 100.0, 2)

        return BaselineComparison(
            baseline_heat_loss_kwh=baseline.total_heat_loss_kwh,
            optimized_heat_loss_kwh=optimized.total_heat_loss_kwh,
            heat_loss_improvement_percent=pct_improvement(
                baseline.total_heat_loss_kwh, optimized.total_heat_loss_kwh
            ),
            baseline_comfort_percentage=baseline.comfort_percentage,
            optimized_comfort_percentage=optimized.comfort_percentage,
            comfort_improvement_points=round(
                optimized.comfort_percentage - baseline.comfort_percentage, 2
            ),
            baseline_heating_requirement_kwh=baseline.estimated_heating_requirement_kwh,
            optimized_heating_requirement_kwh=optimized.estimated_heating_requirement_kwh,
            heating_requirement_improvement_percent=pct_improvement(
                baseline.estimated_heating_requirement_kwh,
                optimized.estimated_heating_requirement_kwh,
            ),
        )

    def run_design_analysis(self, request: ShelterDesignRequest) -> EngineeringReport:
        # 1. Validation happens via Pydantic on ShelterDesignRequest construction;
        #    re-assert the invariant here so orchestration fails fast and clearly.
        if request.comfort_range.max_c <= request.comfort_range.min_c:
            raise ValueError("Invalid comfort range: max_c must exceed min_c")

        # 2. Obtain climate data
        climate = self._climate_provider.get_climate_profile(
            request.location, request.climate_description
        )

        # 3. Generate candidate shelter designs (+ baseline)
        candidates = self._optimizer.generate_candidates(request, climate)
        baseline_design = self._optimizer.generate_baseline(request, climate)
        if not candidates:
            raise ValueError("Design optimizer returned no candidate designs")

        # 4. Evaluate thermal performance for baseline and all candidates
        baseline_performance = self._thermal_simulator.simulate(
            design=baseline_design,
            climate=climate,
            comfort_range=request.comfort_range,
            duration_hours=request.simulation_duration_hours,
        )
        candidate_performances = [
            self._thermal_simulator.simulate(
                design=c,
                climate=climate,
                comfort_range=request.comfort_range,
                duration_hours=request.simulation_duration_hours,
            )
            for c in candidates
        ]

        # 5 & 6. Rank candidates and select the top one
        ranked = sorted(
            zip(candidates, candidate_performances),
            key=lambda pair: pair[1].overall_score,
            reverse=True,
        )
        top_design, top_performance = ranked[0]

        # 7. Optionally validate the top candidate via the ANSYS interface
        ansys_result = None
        if request.run_ansys_validation:
            job_id = self._ansys_validator.validate_design(top_design)
            ansys_result = self._ansys_validator.get_validation_results(job_id, top_design)

        # Robustness across alternate scenarios
        scenarios = self._climate_provider.get_scenarios(climate)
        robustness = evaluate_robustness(
            design=top_design,
            climate=climate,
            scenarios=scenarios,
            thermal_simulator=self._thermal_simulator,
            comfort_range=request.comfort_range,
            duration_hours=request.simulation_duration_hours,
        )

        # Baseline vs optimized comparison
        comparison = self._compare(baseline_performance, top_performance)

        # Confidence assessment
        confidence = assess_confidence(climate, robustness, ansys_result)

        # 8. Recommendation
        recommendation = generate_recommendation(top_design, top_performance, comparison, robustness)

        # 9. Structured final result
        project_meta = {
            "name": "AI-Based Passive Shelter Design — Phase 7 Orchestration",
            "candidates_evaluated": len(candidates),
            "objectives": request.objectives,
            "budget": request.budget,
            "available_materials": request.available_materials,
        }
        design_input = {
            "location": request.location,
            "climate_description": request.climate_description,
            "comfort_range_c": [request.comfort_range.min_c, request.comfort_range.max_c],
            "simulation_duration_hours": request.simulation_duration_hours,
        }
        simulation_meta = {
            "duration_hours": request.simulation_duration_hours,
            "candidates_evaluated": len(candidates),
            "top_design_id": top_design.design_id,
        }

        return EngineeringReport(
            project=project_meta,
            location=request.location,
            climate=climate,
            design_input=design_input,
            simulation=simulation_meta,
            recommended_design=top_design,
            baseline_design=baseline_design,
            results=top_performance,
            baseline_results=baseline_performance,
            comparison=comparison,
            robustness=robustness,
            ansys_validation=ansys_result,
            confidence=confidence,
            recommendation=recommendation,
            assumptions=list(ASSUMPTIONS),
            limitations=list(LIMITATIONS),
        )
