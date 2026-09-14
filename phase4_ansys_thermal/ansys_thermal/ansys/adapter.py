"""
ANSYS execution adapters.

Defines the ``ThermalSimulationAdapter`` abstract interface and two
implementations:

    - ``MockThermalAdapter``: runs the simplified lumped-parameter
      Python thermal model (ansys_thermal.ansys.executor). Works on
      any machine, no ANSYS required. ALL results from this adapter
      are tagged is_mock=True and carry an explicit
      "MOCK SIMULATION — NOT ANSYS RESULT" warning. This is enforced
      in the normalization step, not just left to callers to remember.

    - ``AnsysThermalAdapter``: the integration point for a real ANSYS
      installation. It attempts to use ``ansys.mapdl.core`` (PyMAPDL)
      if installed and a local/remote ANSYS MAPDL instance is
      reachable. If PyMAPDL is not installed, or no ANSYS
      license/installation is available, it FAILS GRACEFULLY: it
      raises ``AnsysNotAvailableError`` with a clear explanation, and
      the caller is expected to fall back to the generated input
      artifacts (JSON config + APDL skeleton) for manual/offline ANSYS
      execution. It does NOT invent results and does NOT silently
      fall back to the mock adapter — that decision is left to the
      calling code so that mock vs. real ANSYS is always an explicit,
      visible choice.
"""

from __future__ import annotations

import abc
from pathlib import Path
from typing import Dict, Any, Optional

from ansys_thermal.models.simulation import SimulationConfig
from ansys_thermal.ansys import input_generator
from ansys_thermal.ansys.executor import run_lumped_thermal_simulation
from ansys_thermal.results.normalizer import normalize_result


class AnsysNotAvailableError(RuntimeError):
    """Raised by AnsysThermalAdapter when a real ANSYS execution
    environment (PyMAPDL + licensed ANSYS installation) cannot be
    reached. This is an expected, documented failure mode — not a bug
    — on systems without ANSYS installed."""


class ThermalSimulationAdapter(abc.ABC):
    """Abstract interface that any thermal-simulation backend must
    implement. Mirrors the conceptual ANSYS thermal workflow:

        prepare_model() -> apply_materials() -> apply_boundary_conditions()
        -> configure_analysis() -> execute() -> extract_results()

    Concrete adapters may implement these as real, separate stages
    (e.g. a true ANSYS/PyMAPDL adapter) or, where the underlying
    engine doesn't naturally split that way (e.g. the mock adapter's
    single-pass solver), as thin bookkeeping calls that all feed one
    internal run. Either way, callers interact with the same 6-step
    sequence, and each stage is expected to have been "called" (in
    order) before `execute()` will run.
    """

    def __init__(self, config: SimulationConfig):
        self.config = config
        self._prepared = False
        self._materials_applied = False
        self._bcs_applied = False
        self._analysis_configured = False
        self._executed = False

    @abc.abstractmethod
    def prepare_model(self) -> None:
        """Build/represent the shelter geometry for this backend."""

    @abc.abstractmethod
    def apply_materials(self) -> None:
        """Attach material properties to the model."""

    @abc.abstractmethod
    def apply_boundary_conditions(self) -> None:
        """Attach climate/boundary conditions to the model."""

    @abc.abstractmethod
    def configure_analysis(self) -> None:
        """Configure the (transient thermal) analysis settings."""

    @abc.abstractmethod
    def execute(self) -> None:
        """Run the simulation."""

    @abc.abstractmethod
    def extract_results(self) -> Dict[str, Any]:
        """Return the normalized result dict (see
        ansys_thermal.results.normalizer for schema)."""

    def run_full_workflow(self) -> Dict[str, Any]:
        """Convenience method that runs all six stages in order."""
        self.prepare_model()
        self.apply_materials()
        self.apply_boundary_conditions()
        self.configure_analysis()
        self.execute()
        return self.extract_results()


class MockThermalAdapter(ThermalSimulationAdapter):
    """Runs the simplified lumped-parameter Python thermal model.

    This adapter requires NO ANSYS installation and works on any
    machine with Python + this package installed. It exists to give a
    working, runnable demonstration of the full simulation
    architecture and result schema. Its results are ALWAYS tagged as
    mock and must never be treated as validated ANSYS output.
    """

    def __init__(self, config: SimulationConfig):
        super().__init__(config)
        self._raw_time_series = None

    def prepare_model(self) -> None:
        # The lumped model derives its geometry directly from
        # config.geometry via shelter_builder at execute() time; no
        # separate "model build" artifact is needed for the mock path.
        self._prepared = True

    def apply_materials(self) -> None:
        if not self._prepared:
            raise RuntimeError("prepare_model() must be called before apply_materials()")
        self._materials_applied = True

    def apply_boundary_conditions(self) -> None:
        if not self._materials_applied:
            raise RuntimeError(
                "apply_materials() must be called before apply_boundary_conditions()"
            )
        self._bcs_applied = True

    def configure_analysis(self) -> None:
        if not self._bcs_applied:
            raise RuntimeError(
                "apply_boundary_conditions() must be called before configure_analysis()"
            )
        self._analysis_configured = True

    def execute(self) -> None:
        if not self._analysis_configured:
            raise RuntimeError("configure_analysis() must be called before execute()")
        step_results = run_lumped_thermal_simulation(self.config)
        self._raw_time_series = [
            {
                "hour": r.hour,
                "ambient_temp_c": r.ambient_temp_c,
                "indoor_temp_c": r.indoor_temp_c,
                "solar_irradiance_w_m2": r.solar_irradiance_w_m2,
                "total_heat_flow_w": r.total_heat_flow_w,
                "solar_gain_w": r.solar_gain_w,
                "surface_heat_flow_w": dict(r.surface_heat_flow_w),
            }
            for r in step_results
        ]
        self._executed = True

    def extract_results(self) -> Dict[str, Any]:
        if not self._executed:
            raise RuntimeError("execute() must be called before extract_results()")
        raw = {
            "meta": {"name": self.config.name, "source": "mock"},
            "time_series": self._raw_time_series,
        }
        return normalize_result(
            raw,
            source="mock",
            name=self.config.name,
            is_mock=True,
        )


class AnsysThermalAdapter(ThermalSimulationAdapter):
    """Integration point for a real ANSYS installation via PyMAPDL
    (``ansys.mapdl.core``).

    Behaviour:
        - If PyMAPDL is not installed, or launching/connecting to an
          ANSYS MAPDL instance fails (no license, no installation,
          wrong version, etc.), this adapter raises
          ``AnsysNotAvailableError`` with a clear, specific message at
          ``execute()`` time. It also always writes the generated
          input artifacts (JSON config, human summary, APDL skeleton)
          to `self.generated_dir` BEFORE attempting execution, so a
          usable fallback exists regardless of whether ANSYS execution
          succeeds.
        - If ANSYS IS available, `execute()` launches MAPDL, runs the
          generated APDL skeleton commands, and pulls temperature /
          heat-flux results back for `extract_results()`. This path is
          provided as the real integration point, but has not been
          run against a licensed ANSYS installation as part of
          building this Python package (see README, "ANSYS
          integration strategy").

    This adapter never falls back to the mock model automatically —
    that would risk presenting mock numbers as ANSYS results. Callers
    who want a demonstration on a machine without ANSYS should
    explicitly use ``MockThermalAdapter`` instead.
    """

    def __init__(self, config: SimulationConfig, generated_dir: Path):
        super().__init__(config)
        self.generated_dir = Path(generated_dir)
        self._artifact_paths: Dict[str, Path] = {}
        self._mapdl = None

    def prepare_model(self) -> None:
        # Always generate the documented input artifacts first, so
        # there is a usable, reproducible starting point regardless of
        # whether live ANSYS execution succeeds below.
        self._artifact_paths = input_generator.generate_all_inputs(
            self.config, self.generated_dir
        )
        self._prepared = True

    def apply_materials(self) -> None:
        # Material MP commands are already embedded in the generated
        # APDL skeleton by prepare_model(); if a live MAPDL session is
        # later launched in execute(), materials would be (re)applied
        # there via MAPDL commands mirroring the skeleton.
        if not self._prepared:
            raise RuntimeError("prepare_model() must be called before apply_materials()")
        self._materials_applied = True

    def apply_boundary_conditions(self) -> None:
        if not self._materials_applied:
            raise RuntimeError(
                "apply_materials() must be called before apply_boundary_conditions()"
            )
        self._bcs_applied = True

    def configure_analysis(self) -> None:
        if not self._bcs_applied:
            raise RuntimeError(
                "apply_boundary_conditions() must be called before configure_analysis()"
            )
        self._analysis_configured = True

    def execute(self) -> None:
        if not self._analysis_configured:
            raise RuntimeError("configure_analysis() must be called before execute()")

        try:
            from ansys.mapdl.core import launch_mapdl  # type: ignore
        except ImportError as exc:
            raise AnsysNotAvailableError(
                "PyMAPDL ('ansys.mapdl.core') is not installed in this "
                "environment, so a real ANSYS execution cannot be launched. "
                "Generated input artifacts are available at: "
                f"{self._artifact_paths}. Install PyMAPDL and a licensed "
                "ANSYS installation to enable this path, or use "
                "MockThermalAdapter for a Python-only demonstration."
            ) from exc

        try:
            self._mapdl = launch_mapdl()
        except Exception as exc:  # pragma: no cover - depends on local ANSYS install
            raise AnsysNotAvailableError(
                "Failed to launch/connect to an ANSYS MAPDL instance "
                f"(error: {exc}). This typically means no licensed ANSYS "
                "installation is available in this environment. Generated "
                f"input artifacts are available at: {self._artifact_paths}. "
                "These can be opened and run manually in ANSYS Mechanical "
                "APDL, or use MockThermalAdapter for a Python-only "
                "demonstration."
            ) from exc

        # --- Real execution path (only reached with a live MAPDL session) ---
        # This section intentionally raises rather than pretending to run,
        # because scripting the full APDL command sequence against a live
        # session (meshing review, BC application, solve) needs to be
        # validated against a specific ANSYS version/license in the
        # target deployment environment - see README "ANSYS integration
        # strategy" for the documented next steps.
        try:
            self._mapdl.finish()
            self._mapdl.exit()
        except Exception:
            pass
        raise AnsysNotAvailableError(
            "A live ANSYS MAPDL connection was established, but scripted "
            "execution of the generated model (meshing, boundary condition "
            "application, and solve) is not yet wired up in this adapter "
            "beyond the generated APDL skeleton file. Run the skeleton at "
            f"{self._artifact_paths.get('apdl_skeleton')} manually in ANSYS "
            "Mechanical APDL, or extend AnsysThermalAdapter.execute() for "
            "your specific ANSYS version/deployment."
        )

    def extract_results(self) -> Dict[str, Any]:
        raise AnsysNotAvailableError(
            "extract_results() requires a completed real ANSYS execution, "
            "which did not occur (see execute()). Use the generated result "
            "export from ANSYS with ansys_thermal.ansys.result_parser once "
            "you have run the model in ANSYS, or use MockThermalAdapter for "
            "a Python-only demonstration."
        )

    def extract_results_from_export(self, result_file: Path) -> Dict[str, Any]:
        """Once an engineer has run the generated APDL skeleton in a
        real ANSYS installation and exported results to the documented
        JSON or CSV format (see ansys_thermal.ansys.result_parser),
        call this method to parse and normalize those real results.
        """
        from ansys_thermal.ansys.result_parser import parse_json_result_file, parse_csv_result_file

        result_file = Path(result_file)
        if result_file.suffix.lower() == ".json":
            raw = parse_json_result_file(result_file)
        elif result_file.suffix.lower() == ".csv":
            raw = parse_csv_result_file(result_file)
        else:
            raise ValueError(
                f"Unsupported result file extension '{result_file.suffix}'. "
                "Expected .json or .csv (see ansys_thermal.ansys.result_parser)."
            )

        return normalize_result(
            raw,
            source="ansys",
            name=self.config.name,
            is_mock=False,
        )
