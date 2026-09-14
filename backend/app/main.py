"""
Passive Shelter API - Phase 10 backend/API layer.

Standalone FastAPI application. See README.md for details.
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import logger
from app.services.simulation_backend import SimulationBackendUnavailableError

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "AI-Based Software Model for Designing Energy-Efficient Passive Shelters — "
        "Phase 10 FastAPI backend/API layer. All lower-level engines (thermal, "
        "optimization, ANSYS) are mocked/abstracted for standalone operation."
    ),
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("%s %s", request.method, request.url.path)
    response = await call_next(request)
    logger.info("%s %s -> %s", request.method, request.url.path, response.status_code)
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    payload = jsonable_encoder(exc.errors())
    logger.warning("Validation error on %s: %s", request.url.path, payload)
    return JSONResponse(
        status_code=422,
        content={"detail": payload, "message": "Invalid input"},
    )


@app.exception_handler(SimulationBackendUnavailableError)
async def simulation_backend_unavailable_handler(request: Request, exc: SimulationBackendUnavailableError):
    logger.error("Simulation backend unavailable: %s", exc)
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        raise exc
    logger.error("Unhandled error on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.include_router(api_router)


@app.get("/", tags=["root"], summary="Root")
def root():
    return {
        "message": f"{settings.app_name} is running",
        "docs": "/docs",
        "api_prefix": "/api/v1",
    }
