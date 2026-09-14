import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app.mocks.ansys import MockANSYSValidator
from app.mocks.climate import MockClimateProvider
from app.mocks.optimizer import MockDesignOptimizer
from app.mocks.thermal import MockThermalSimulator
from app.models.request import ComfortRange, ShelterDesignRequest
from app.services.orchestrator import Orchestrator


@pytest.fixture
def climate_provider():
    return MockClimateProvider()


@pytest.fixture
def thermal_simulator():
    return MockThermalSimulator()


@pytest.fixture
def optimizer():
    return MockDesignOptimizer()


@pytest.fixture
def ansys_validator():
    return MockANSYSValidator()


@pytest.fixture
def orchestrator(climate_provider, thermal_simulator, optimizer, ansys_validator):
    return Orchestrator(
        climate_provider=climate_provider,
        thermal_simulator=thermal_simulator,
        optimizer=optimizer,
        ansys_validator=ansys_validator,
    )


@pytest.fixture
def ladakh_request():
    return ShelterDesignRequest(
        location="Ladakh",
        climate_description="cold high-altitude",
        comfort_range=ComfortRange(min_c=18, max_c=26),
        simulation_duration_hours=24,
    )
