"""FastAPI service exposing the Phase 7 orchestration engine.

Run with:
    uvicorn app.main:app --reload
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ValidationError

from app.interfaces.ansys import ANSYSValidator
from app.interfaces.climate import ClimateProvider
from app.interfaces.optimizer import DesignOptimizer
from app.interfaces.thermal import ThermalSimulator
from app.mocks.ansys import MockANSYSValidator
from app.mocks.climate import MockClimateProvider
from app.mocks.optimizer import MockDesignOptimizer
from app.mocks.thermal import MockThermalSimulator
from app.models.report import EngineeringReport
from app.models.request import CompareRequest, ShelterDesignRequest, WhatIfRequest
from app.models.results import WhatIfResult
from app.services.orchestrator import Orchestrator
from app.services.what_if import apply_what_if

app = FastAPI(
    title="Passive Shelter Design — Phase 7 Orchestration Engine",
    description=(
        "Orchestration and decision layer coordinating climate data, thermal "
        "simulation, design optimization, and engineering recommendations. "
        "This service currently runs entirely on MOCK components — see README."
    ),
    version="7.0.0",
)

# --- Dependency wiring -----------------------------------------------------
# The orchestrator is constructed once with concrete mock implementations
# injected through the abstract interfaces. Swapping in real components
# later means changing only these four lines.
_climate_provider: ClimateProvider = MockClimateProvider()
_thermal_simulator: ThermalSimulator = MockThermalSimulator()
_optimizer: DesignOptimizer = MockDesignOptimizer()
_ansys_validator: ANSYSValidator = MockANSYSValidator()

_orchestrator = Orchestrator(
    climate_provider=_climate_provider,
    thermal_simulator=_thermal_simulator,
    optimizer=_optimizer,
    ansys_validator=_ansys_validator,
)


class HealthResponse(BaseModel):
    status: str
    mock_mode: bool
    version: str


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", mock_mode=True, version="7.0.0")


@app.post("/api/analyze", response_model=EngineeringReport)
def analyze(request: ShelterDesignRequest) -> EngineeringReport:
    try:
        return _orchestrator.run_design_analysis(request)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/what-if", response_model=WhatIfResult)
def what_if(request: WhatIfRequest) -> WhatIfResult:
    try:
        climate = _climate_provider.get_climate_profile(request.location, request.climate_description)
        candidates = _optimizer.generate_candidates(
            ShelterDesignRequest(
                location=request.location,
                climate_description=request.climate_description,
                comfort_range=request.comfort_range,
            ),
            climate,
        )
        base_design = candidates[0]
        if request.base_design_id:
            for c in candidates:
                if c.design_id == request.base_design_id:
                    base_design = c
                    break
        return apply_what_if(
            base_design=base_design,
            parameter=request.parameter,
            new_value=request.new_value,
            climate=climate,
            comfort_range=request.comfort_range,
            duration_hours=24,
            thermal_simulator=_thermal_simulator,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/compare")
def compare(request: CompareRequest) -> dict:
    climate = _climate_provider.get_climate_profile(request.location, request.climate_description)
    candidates = _optimizer.generate_candidates(
        ShelterDesignRequest(
            location=request.location,
            climate_description=request.climate_description,
            comfort_range=request.comfort_range,
        ),
        climate,
    )
    baseline = _optimizer.generate_baseline(
        ShelterDesignRequest(
            location=request.location,
            climate_description=request.climate_description,
            comfort_range=request.comfort_range,
        ),
        climate,
    )
    pool = {d.design_id: d for d in candidates + [baseline]}

    ids = request.design_ids or list(pool.keys())[:3]
    results = []
    for design_id in ids:
        design = pool.get(design_id)
        if design is None:
            raise HTTPException(status_code=404, detail=f"Unknown design_id: {design_id}")
        perf = _thermal_simulator.simulate(
            design=design,
            climate=climate,
            comfort_range=request.comfort_range,
            duration_hours=24,
        )
        results.append({"design": design.model_dump(), "performance": perf.model_dump()})

    return {"location": request.location, "compared": results}


@app.get("/api/demo")
def demo() -> EngineeringReport:
    request = ShelterDesignRequest(
        location="Ladakh",
        climate_description="cold high-altitude",
        comfort_range={"min_c": 18, "max_c": 26},
        simulation_duration_hours=24,
    )
    return _orchestrator.run_design_analysis(request)
