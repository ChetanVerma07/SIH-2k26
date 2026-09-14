"""
ANSYS input generation.

This module generates machine-readable and human-readable artifacts
that describe a simulation, WITHOUT requiring an ANSYS installation:

    1. A JSON configuration file capturing geometry, materials, climate,
       and boundary conditions (documented schema — see README).
    2. A human-readable text summary of the simulation setup.
    3. A skeleton ANSYS Mechanical APDL (.dat) input file that an
       engineer can open in ANSYS Mechanical APDL / batch-run with
       `ansys2xx -b -i model.dat -o model.out` to build the actual
       model.

IMPORTANT — scope and honesty about capability:
    The generated .dat file is a STARTING-POINT SKELETON. It sets up
    element types, material properties (MP commands), and key
    parameters (dimensions, convection coefficients, ambient
    temperatures) as APDL parameters, and lays out the documented
    manual/scripted steps (geometry creation via BLOCK, meshing via
    VMESH, boundary conditions via SF/SFE, solving via time-stepped
    TRANS thermal solve). It is NOT a fully meshed, solver-ready model
    produced by a headless ANSYS process, because that requires an
    actual licensed ANSYS installation to generate/validate. This is
    intentional and documented — see README section "What requires
    manual ANSYS setup".
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

from ansys_thermal.models.simulation import SimulationConfig
from ansys_thermal.geometry.shelter_builder import (
    build_rectangular_shelter,
    ShelterBuildPlan,
)


def generate_json_config(config: SimulationConfig, output_path: Path) -> Path:
    """Write the full simulation configuration as JSON.

    This is the canonical machine-readable artifact: any adapter
    (mock or real ANSYS) can be driven purely from this file, and any
    engineer can reproduce the simulation setup from it alone.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(config.as_dict(), f, indent=2)
    return output_path


def generate_human_summary(config: SimulationConfig, output_path: Path) -> Path:
    """Write a human-readable plain-text summary of the simulation
    configuration, intended for an engineer reviewing the setup before
    running it in ANSYS."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    g = config.geometry
    bc = config.boundary_conditions
    m = config.materials

    lines = [
        f"SIMULATION CONFIGURATION SUMMARY",
        f"=================================",
        f"Name            : {config.name}",
        f"Analysis type   : {config.analysis_type}",
        f"Notes           : {config.notes or '(none)'}",
        "",
        "GEOMETRY (rectangular shelter)",
        "-------------------------------",
        f"  Length x Width x Height : {g.length} m x {g.width} m x {g.height} m",
        f"  Wall thickness          : {g.wall_thickness} m",
        f"  Roof thickness          : {g.roof_thickness} m",
        f"  Floor thickness         : {g.floor_thickness} m",
        f"  Window area             : {g.window_area} m^2",
        f"  Door area               : {g.door_area} m^2",
        f"  Other openings area     : {g.other_openings_area} m^2",
        f"  Orientation             : {g.orientation_deg} deg from North",
        f"  Floor area (derived)    : {g.floor_area():.2f} m^2",
        f"  Internal volume(derived): {g.internal_volume():.2f} m^3",
        f"  Net wall area (derived) : {g.wall_net_area():.2f} m^2",
        "",
        "MATERIALS",
        "---------",
        f"  Wall   : {m.wall_material.name}  (k={m.wall_material.thermal_conductivity_w_mk} W/m.K, "
        f"rho={m.wall_material.density_kg_m3} kg/m3, cp={m.wall_material.specific_heat_j_kgk} J/kg.K)",
        f"  Roof   : {m.roof_material.name}  (k={m.roof_material.thermal_conductivity_w_mk} W/m.K)",
        f"  Floor  : {m.floor_material.name}  (k={m.floor_material.thermal_conductivity_w_mk} W/m.K)",
        f"  Window : {m.window_material.name}  (k={m.window_material.thermal_conductivity_w_mk} W/m.K)",
        "",
        "BOUNDARY CONDITIONS",
        "--------------------",
        f"  Indoor initial temperature : {bc.indoor_initial_temp_c} degC",
        f"  Internal convection coeff. : {bc.internal_convection_w_m2k} W/m2.K",
        f"  External convection coeff. : {bc.external_convection_w_m2k} W/m2.K",
        f"  Ground temperature         : {bc.ground_temp_c} degC",
        f"  Time step                  : {bc.time_step_s} s",
        f"  Duration                   : {bc.duration_hours} hours",
        f"  Ambient series points      : {len(bc.ambient_series)}",
        (
            f"  Ambient temp range         : "
            f"{min(p.ambient_temp_c for p in bc.ambient_series):.1f} to "
            f"{max(p.ambient_temp_c for p in bc.ambient_series):.1f} degC"
        ),
        (
            f"  Peak solar irradiance      : "
            f"{max(p.solar_irradiance_w_m2 for p in bc.ambient_series):.1f} W/m^2"
        ),
        "",
        "This summary was generated automatically from the JSON",
        "configuration file of the same simulation name. It is intended",
        "to let an engineer quickly review a setup before running it,",
        "either via the mock adapter or in an actual ANSYS installation.",
    ]

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def _apdl_header(config: SimulationConfig, plan: ShelterBuildPlan) -> str:
    """Header comment block explaining scope/limitations of the .dat
    skeleton, embedded directly in the file for engineers who open it
    in ANSYS Mechanical APDL."""
    return f"""! =====================================================================
! ANSYS Mechanical APDL skeleton input file
! Auto-generated by ansys_thermal.ansys.input_generator
!
! Simulation name : {config.name}
! Analysis type   : {config.analysis_type}
!
! SCOPE / LIMITATIONS (read before running):
!   - This file sets up parameters, element type, and material
!     properties (MP commands) for a transient thermal analysis of a
!     rectangular shelter.
!   - Geometry creation (BLOCK), meshing (VMESH/ESIZE), and boundary
!     condition application (SF/SFE for convection, radiation, and
!     solar loads) are scripted below using the parameters, but the
!     exact mesh density, contact handling between elements (if the
!     model is split into multiple volumes), and solar-load application
!     method (SFE with time-varying tabular loads) SHOULD be reviewed
!     and adjusted by an engineer in ANSYS Mechanical APDL or Workbench
!     before production use.
!   - This file has NOT been executed or validated against a licensed
!     ANSYS installation as part of this Python package. Treat it as a
!     documented starting point, not a validated solver-ready model.
! =====================================================================

/CLEAR
/TITLE, {config.name}
/PREP7
"""


def generate_apdl_skeleton(config: SimulationConfig, output_path: Path) -> Path:
    """Generate a skeleton ANSYS Mechanical APDL (.dat) input file.

    This produces parameterized APDL commands for:
        - element type (thermal solid, PLANE55/SOLID70-style choice)
        - material properties for wall / roof / floor / window
        - basic block geometry sized from the shelter dimensions
        - convection boundary conditions (internal + external)
        - a transient analysis time-stepping block

    The file is a documented skeleton (see header comment) — a real
    production run requires opening it in ANSYS Mechanical APDL,
    reviewing meshing and load application, and then executing it
    there. This package does not claim to run ANSYS itself.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plan = build_rectangular_shelter(config.geometry)
    g = config.geometry
    m = config.materials
    bc = config.boundary_conditions

    body = [_apdl_header(config, plan)]

    body.append("! --- Element type: 3-D thermal solid ---")
    body.append("ET,1,SOLID70   ! 3-D 8-node thermal solid element")
    body.append("")

    body.append("! --- Material properties (MP commands) ---")
    body.append("! Material 1: Wall")
    body.append(f"MP,KXX,1,{m.wall_material.thermal_conductivity_w_mk}")
    body.append(f"MP,DENS,1,{m.wall_material.density_kg_m3}")
    body.append(f"MP,C,1,{m.wall_material.specific_heat_j_kgk}")
    body.append("! Material 2: Roof")
    body.append(f"MP,KXX,2,{m.roof_material.thermal_conductivity_w_mk}")
    body.append(f"MP,DENS,2,{m.roof_material.density_kg_m3}")
    body.append(f"MP,C,2,{m.roof_material.specific_heat_j_kgk}")
    body.append("! Material 3: Floor")
    body.append(f"MP,KXX,3,{m.floor_material.thermal_conductivity_w_mk}")
    body.append(f"MP,DENS,3,{m.floor_material.density_kg_m3}")
    body.append(f"MP,C,3,{m.floor_material.specific_heat_j_kgk}")
    body.append("! Material 4: Window / opening")
    body.append(f"MP,KXX,4,{m.window_material.thermal_conductivity_w_mk}")
    body.append(f"MP,DENS,4,{m.window_material.density_kg_m3}")
    body.append(f"MP,C,4,{m.window_material.specific_heat_j_kgk}")
    body.append("")

    body.append("! --- Parameterized geometry (rectangular shelter) ---")
    body.append(f"LEN = {g.length}        ! shelter length, m")
    body.append(f"WID = {g.width}         ! shelter width, m")
    body.append(f"HGT = {g.height}        ! shelter height, m")
    body.append(f"TWALL = {g.wall_thickness}   ! wall thickness, m")
    body.append(f"TROOF = {g.roof_thickness}   ! roof thickness, m")
    body.append(f"TFLOOR = {g.floor_thickness} ! floor thickness, m")
    body.append("")
    body.append("! Build outer and inner blocks, subtract to form wall shell.")
    body.append("! (Engineer should review Boolean operations / sizing before meshing.)")
    body.append("BLOCK,0,LEN,0,WID,0,HGT                 ! outer shelter volume")
    body.append("BLOCK,TWALL,LEN-TWALL,TWALL,WID-TWALL,TFLOOR,HGT-TROOF  ! inner air volume")
    body.append("VSBV,1,2      ! subtract inner from outer -> wall+roof+floor shell")
    body.append("")

    body.append("! --- Meshing (review element size before production run) ---")
    body.append("ESIZE,0.1     ! default 0.1 m element size; refine as needed")
    body.append("VMESH,ALL")
    body.append("")

    body.append("! --- Boundary conditions ---")
    body.append(f"TAMB_INIT = {bc.indoor_initial_temp_c}   ! initial indoor temperature, degC")
    body.append(f"HCONV_IN = {bc.internal_convection_w_m2k}   ! internal convection coeff, W/m2.K")
    body.append(f"HCONV_OUT = {bc.external_convection_w_m2k} ! external convection coeff, W/m2.K")
    body.append(f"TGROUND = {bc.ground_temp_c}    ! ground temperature, degC")
    body.append("")
    body.append("! Apply initial condition")
    body.append("IC,ALL,TEMP,TAMB_INIT")
    body.append("")
    body.append("! External convection surfaces: select exterior wall/roof faces, then:")
    body.append("!   SF,ALL,CONV,HCONV_OUT,TAMB_TABLE   (TAMB_TABLE = time-varying ambient,")
    body.append("!   defined via *DIM / tabular load referencing the climate series in the")
    body.append("!   accompanying JSON config)")
    body.append("! Floor: apply TGROUND as a fixed-temperature or convection condition.")
    body.append("! Solar load: apply as surface heat flux (SFE,...,HFLUX,...) scaled by")
    body.append("!   surface solar absorptivity and the solar_irradiance_w_m2 series.")
    body.append("! -- These selections depend on final meshed geometry and are left for")
    body.append("!    the engineer to complete in ANSYS Mechanical APDL / Workbench.")
    body.append("")

    body.append("! --- Analysis configuration: transient thermal ---")
    body.append("/SOLU")
    body.append("ANTYPE,TRANS")
    body.append(f"TIME,{bc.duration_hours * 3600.0}   ! total time, seconds")
    body.append(f"DELTIM,{bc.time_step_s}             ! time step, seconds")
    body.append("KBC,0        ! ramped loading between substeps")
    body.append("AUTOTS,ON")
    body.append("")
    body.append("! SOLVE  ! <-- uncomment to run once BCs/mesh are finalized")
    body.append("")
    body.append("FINISH")

    output_path.write_text("\n".join(body), encoding="utf-8")
    return output_path


def generate_all_inputs(config: SimulationConfig, output_dir: Path) -> Dict[str, Path]:
    """Generate the full set of input artifacts (JSON config, human
    summary, APDL skeleton) for a given simulation configuration into
    `output_dir`. Returns a dict of artifact name -> path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in config.name)

    json_path = generate_json_config(config, output_dir / f"{safe_name}_config.json")
    summary_path = generate_human_summary(config, output_dir / f"{safe_name}_summary.txt")
    apdl_path = generate_apdl_skeleton(config, output_dir / f"{safe_name}_model.dat")

    return {
        "json_config": json_path,
        "human_summary": summary_path,
        "apdl_skeleton": apdl_path,
    }
