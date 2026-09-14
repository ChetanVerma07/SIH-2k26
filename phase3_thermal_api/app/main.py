"""
FastAPI application entrypoint.

Run with:
    uvicorn app.main:app --reload

Interactive docs:
    http://127.0.0.1:8000/docs      (Swagger UI)
    http://127.0.0.1:8000/redoc     (ReDoc)
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from app.data.materials import get_example_materials
from app.models.simulation import CompareRequest, CompareResult, SimulationRequest, SimulationResult
from app.services.comparison_service import run_comparison
from app.services.simulation_service import run_and_summarize

app = FastAPI(
    title="Passive Shelter Thermal Simulation API",
    description=(
        "Phase 3: a standalone physics-based (non-AI/ML) transient thermal "
        "engine for passive shelter design analysis. See README.md for the "
        "governing equations, units, and documented simplifications."
    ),
    version="1.0.0",
)


@app.get("/api/health", tags=["health"])
def health() -> dict:
    """Basic service health check."""
    return {"status": "ok", "service": "phase3-thermal-api", "version": app.version}


@app.get("/api/materials", tags=["materials"])
def materials() -> dict:
    """Return a library of example material definitions."""
    return {name: mat.model_dump() for name, mat in get_example_materials().items()}


@app.post("/api/simulate", response_model=SimulationResult, tags=["simulation"])
def simulate(request: SimulationRequest) -> SimulationResult:
    """
    Run a single transient thermal simulation for one shelter design under
    one climate scenario. See README for the request/response schema and
    example payloads.
    """
    try:
        return run_and_summarize(request.shelter, request)
    except ValidationError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/compare", response_model=CompareResult, tags=["simulation"])
def compare(request: CompareRequest) -> CompareResult:
    """
    Run the thermal simulation for two or more shelter designs under the
    same climate and return them ranked by a configurable weighted score
    of thermal comfort, heat loss, and solar gain.
    """
    try:
        return run_comparison(request)
    except ValidationError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
