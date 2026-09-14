"""
Thermal engine abstraction.

`ThermalEngine` defines the interface the rest of the system depends on.
`MockThermalEngine` is a deterministic, physically-plausible stand-in used
in this phase. A future phase can implement a real physics engine (or wrap
ANSYS results) behind the same interface without touching services/routes.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict

from app.models.climate import ClimateRecord
from app.models.design import ShelterDesign
from app.models.material import Material
from app.models.simulation import SimulationResults


class ThermalEngine(ABC):
    @abstractmethod
    def calculate(
        self,
        design: ShelterDesign,
        climate: ClimateRecord,
        materials: Dict[str, Material],
    ) -> Dict[str, Any]:
        """Perform a single deterministic thermal calculation."""
        raise NotImplementedError

    @abstractmethod
    def simulate(
        self,
        design: ShelterDesign,
        climate: ClimateRecord,
        materials: Dict[str, Material],
        duration: float,
        timestep: float,
    ) -> Dict[str, Any]:
        """Run a time-stepped simulation and return aggregated results."""
        raise NotImplementedError

    @abstractmethod
    def get_results(self, raw_output: Dict[str, Any]) -> SimulationResults:
        """Convert raw engine output into a SimulationResults object."""
        raise NotImplementedError


class MockThermalEngine(ThermalEngine):
    """
    Deterministic mock thermal model.

    Not physically accurate (this is explicitly NOT ANSYS) but follows
    sensible qualitative physics so the rest of the system can be built
    and tested against it:
      - greater insulation thickness -> lower heat loss
      - higher wall thermal conductivity -> higher heat loss
      - greater solar radiation -> higher solar/heat gain
      - larger openings -> greater heat exchange (loss AND gain)
    """

    BACKEND_NAME = "MOCK"

    def _envelope_area(self, design: ShelterDesign) -> float:
        wall_area = 2 * (design.length + design.width) * design.height
        roof_area = design.length * design.width
        return wall_area + roof_area

    def calculate(
        self,
        design: ShelterDesign,
        climate: ClimateRecord,
        materials: Dict[str, Material],
    ) -> Dict[str, Any]:
        wall_material = materials["wall_material"]
        insulation_material = materials["insulation_material"]

        delta_t = climate.temperature - (design.target_min_temperature + design.target_max_temperature) / 2

        # Effective conductive resistance: thicker insulation & lower
        # conductivity materials increase resistance -> reduce heat loss.
        insulation_thickness = max(design.insulation_thickness, 0.001)
        wall_conductivity = wall_material.thermal_conductivity
        insulation_conductivity = insulation_material.thermal_conductivity

        wall_resistance = design.wall_thickness / max(wall_conductivity, 0.001)
        insulation_resistance = insulation_thickness / max(insulation_conductivity, 0.001)
        total_resistance = max(wall_resistance + insulation_resistance, 0.01)

        envelope_area = self._envelope_area(design)
        opening_factor = 1 + (design.opening_percentage / 100.0) * 1.5

        # Conductive/convective heat loss (positive = losing heat to a colder outside)
        heat_loss = abs(delta_t) * envelope_area * opening_factor / total_resistance
        heat_loss = round(heat_loss, 2)

        # Solar gain depends on solar radiation, absorptivity, opening size
        solar_absorptivity = wall_material.solar_absorptivity
        opening_area_fraction = design.opening_percentage / 100.0
        solar_gain = (
            climate.solar_radiation
            * (0.3 + 0.7 * opening_area_fraction)
            * (0.5 + 0.5 * solar_absorptivity)
            * (envelope_area / 100.0)
        )
        solar_gain = round(max(solar_gain, 0.0), 2)

        # Indoor temperature estimate: outdoor temp buffered by resistance,
        # nudged upward by solar gain and downward by heat loss.
        buffering = min(total_resistance / (total_resistance + 1), 0.95)
        indoor_temperature = climate.temperature + buffering * (delta_t * -0.5)
        indoor_temperature += (solar_gain - heat_loss) / max(envelope_area, 1) * 0.05
        indoor_temperature = round(indoor_temperature, 2)

        return {
            "indoor_temperature": indoor_temperature,
            "outdoor_temperature": climate.temperature,
            "heat_loss": heat_loss,
            "solar_gain": solar_gain,
            "total_resistance": total_resistance,
            "envelope_area": envelope_area,
        }

    def simulate(
        self,
        design: ShelterDesign,
        climate: ClimateRecord,
        materials: Dict[str, Material],
        duration: float,
        timestep: float,
    ) -> Dict[str, Any]:
        steps = max(int(duration / max(timestep, 0.01)), 1)
        steps = min(steps, 2000)  # safety cap for the mock engine

        base = self.calculate(design, climate, materials)

        temperatures = []
        heat_losses = []
        solar_gains = []

        for i in range(steps):
            # Deterministic diurnal-like oscillation based on step index.
            cycle_position = (i % 24) / 24.0
            solar_multiplier = max(0.0, 1.0 - abs(cycle_position - 0.5) * 2) * 1.4
            temp_wave = 2.0 * ((i % 24) - 12) / 12.0

            step_indoor = base["indoor_temperature"] + temp_wave * 0.3
            step_solar_gain = round(base["solar_gain"] * solar_multiplier, 2)
            step_heat_loss = round(base["heat_loss"] * (1 + abs(temp_wave) * 0.1), 2)

            temperatures.append(round(step_indoor, 2))
            heat_losses.append(step_heat_loss)
            solar_gains.append(step_solar_gain)

        average_temperature = round(sum(temperatures) / len(temperatures), 2)
        minimum_temperature = round(min(temperatures), 2)
        maximum_temperature = round(max(temperatures), 2)
        total_heat_loss = round(sum(heat_losses), 2)
        total_solar_gain = round(sum(solar_gains), 2)

        comfortable_steps = sum(
            1
            for t in temperatures
            if design.target_min_temperature <= t <= design.target_max_temperature
        )
        comfort_percentage = round(100.0 * comfortable_steps / len(temperatures), 2)

        return {
            "indoor_temperature": base["indoor_temperature"],
            "outdoor_temperature": base["outdoor_temperature"],
            "heat_loss": base["heat_loss"],
            "solar_gain": base["solar_gain"],
            "average_temperature": average_temperature,
            "minimum_temperature": minimum_temperature,
            "maximum_temperature": maximum_temperature,
            "comfort_percentage": comfort_percentage,
            "total_heat_loss": total_heat_loss,
            "total_solar_gain": total_solar_gain,
        }

    def get_results(self, raw_output: Dict[str, Any]) -> SimulationResults:
        return SimulationResults(
            indoor_temperature=raw_output["indoor_temperature"],
            outdoor_temperature=raw_output["outdoor_temperature"],
            heat_loss=raw_output["heat_loss"],
            solar_gain=raw_output["solar_gain"],
            average_temperature=raw_output["average_temperature"],
            minimum_temperature=raw_output["minimum_temperature"],
            maximum_temperature=raw_output["maximum_temperature"],
            comfort_percentage=raw_output["comfort_percentage"],
            total_heat_loss=raw_output["total_heat_loss"],
            total_solar_gain=raw_output["total_solar_gain"],
        )
