"""
Phase 8 - ANSYSBackend.

Real integration with ANSYS Mechanical APDL (MAPDL), run in headless batch
mode. This backend is fully configurable (executable path, working dir,
core count, license server) via SimulationSettings so it can be pointed at
whatever ANSYS install is available on the machine actually running it.

It reuses the exact same .inp file produced by core.input_generator (the
same one MockANSYSBackend "would" run), so switching backend never changes
the model definition -- only who solves it.

This class deliberately fails fast and clearly (is_available() / run())
rather than silently falling back to guesses, since giving a wrong
"success" from a missing ANSYS install would be worse than no result.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time

from backend.simulation_backend import SimulationBackend, BackendRunResult, RunStatus
from core.input_generator import generate_apdl_input


class ANSYSBackend(SimulationBackend):
    name = "ansys_real"

    def __init__(self, exe_path: str = None, working_dir: str = None,
                 num_cores: int = 2, license_server: str = None,
                 timeout_s: int = 1800):
        # exe_path may be a bare command ("ansys2024R1", "mapdl") resolvable
        # via PATH, or a full path to the executable.
        self.exe_path = exe_path or "mapdl"
        self.working_dir = working_dir
        self.num_cores = num_cores
        self.license_server = license_server
        self.timeout_s = timeout_s

    def is_available(self) -> bool:
        """Check the executable resolves on PATH (or exists at the given
        path) so we never claim to "run" ANSYS when it isn't installed."""
        if os.path.isabs(self.exe_path):
            return os.path.isfile(self.exe_path) and os.access(self.exe_path, os.X_OK)
        return shutil.which(self.exe_path) is not None

    def prepare_input(self, case_dir: str, design, climate, settings) -> str:
        # Same generator as the mock backend -- the real .inp is produced
        # up front, before we ever try to invoke ANSYS, so it is available
        # even if the solve step below fails or is skipped.
        return generate_apdl_input(case_dir, design, climate, settings)

    def _build_command(self, input_file: str, out_file: str) -> list:
        # Standard MAPDL batch invocation:
        #   mapdl -b -np <cores> -i <input>.inp -o <output>.out
        cmd = [self.exe_path, "-b", "-np", str(self.num_cores),
               "-i", input_file, "-o", out_file]
        return cmd

    def run(self, case_dir: str, input_file: str, settings) -> BackendRunResult:
        start = time.time()

        if not self.is_available():
            return BackendRunResult(
                status=RunStatus.FAILED,
                error_message=(
                    f"ANSYS executable '{self.exe_path}' not found on this "
                    "machine. The .inp file has still been generated at "
                    f"'{input_file}' and can be run on a licensed ANSYS "
                    "workstation, or you can switch to MockANSYSBackend "
                    "for a demo run."
                ),
                wall_clock_s=0.0,
            )

        env = os.environ.copy()
        if self.license_server:
            env["ANSYSLMD_LICENSE_FILE"] = self.license_server

        out_log = os.path.join(case_dir, "ansys_solve.out")
        cmd = self._build_command(input_file, out_log)

        try:
            proc = subprocess.run(
                cmd,
                cwd=self.working_dir or case_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=self.timeout_s,
            )
        except FileNotFoundError as exc:
            return BackendRunResult(
                status=RunStatus.FAILED,
                error_message=f"Failed to launch ANSYS: {exc}",
                wall_clock_s=time.time() - start,
            )
        except subprocess.TimeoutExpired as exc:
            return BackendRunResult(
                status=RunStatus.FAILED,
                error_message=f"ANSYS solve timed out after {self.timeout_s}s: {exc}",
                wall_clock_s=time.time() - start,
            )

        elapsed = time.time() - start
        results_path = os.path.join(case_dir, "ansys_results.csv")

        if proc.returncode != 0 or not os.path.exists(results_path):
            return BackendRunResult(
                status=RunStatus.FAILED,
                raw_log=proc.stdout + "\n" + proc.stderr,
                error_message=(
                    f"ANSYS exited with code {proc.returncode} or did not "
                    f"produce expected results file '{results_path}'. "
                    "Check ansys_solve.out in the case directory."
                ),
                wall_clock_s=elapsed,
            )

        return BackendRunResult(
            status=RunStatus.COMPLETED,
            results_file=results_path,
            raw_log=proc.stdout,
            wall_clock_s=elapsed,
        )
