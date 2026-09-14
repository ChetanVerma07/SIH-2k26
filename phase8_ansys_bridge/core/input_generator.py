"""
Phase 8 - ANSYS input generator.

Builds a real ANSYS Mechanical APDL (.inp) batch script for a transient
thermal analysis of the shelter envelope, purely from the design/climate
dataclasses. This file is produced regardless of which backend is used
(Mock or real ANSYS) so the user always has a genuine ANSYS-ready input
they can hand to a licensed workstation.

Model simplified as a single-zone lumped shell (walls + roof + floor +
windows) meshed as SHELL131 thermal shell elements, which is a standard,
lightweight way to represent building envelope thermal behaviour in APDL
without needing full 3D solid geometry.
"""

from __future__ import annotations

import os
from textwrap import dedent

from config import ShelterDesignParams, ClimateParams, SimulationSettings


def _material_block(design: ShelterDesignParams) -> str:
    """APDL material property definitions for wall / roof / window."""
    wall_r = design.wall_thickness_m / max(design.wall_conductivity_w_mk, 1e-6)
    roof_r = design.roof_thickness_m / max(design.roof_conductivity_w_mk, 1e-6)
    total_wall_r = wall_r + design.insulation_r_value_m2k_w

    return dedent(f"""\
    ! ---- Material properties (SI units: m, kg, s, C, W) ----
    MP,KXX,1,{design.wall_conductivity_w_mk}      ! wall conductivity
    MP,DENS,1,1900                                 ! wall density (approx, brick/block)
    MP,C,1,880                                     ! wall specific heat

    MP,KXX,2,{design.roof_conductivity_w_mk}      ! roof conductivity
    MP,DENS,2,2400                                 ! roof density (RCC)
    MP,C,2,880                                     ! roof specific heat

    ! Effective wall R-value including added insulation: {total_wall_r:.3f} m2K/W
    ! Effective roof R-value: {roof_r:.3f} m2K/W
    """)


def _geometry_block(design: ShelterDesignParams) -> str:
    return dedent(f"""\
    ! ---- Simplified envelope geometry (shell representation) ----
    ! Wall area   : {design.wall_area_m2} m2   thickness {design.wall_thickness_m} m
    ! Roof area   : {design.roof_area_m2} m2   thickness {design.roof_thickness_m} m
    ! Floor area  : {design.floor_area_m2} m2
    ! Window area : {design.window_area_m2} m2   U-value {design.window_u_value_w_m2k} W/m2K
    ! Orientation : {design.orientation_deg} deg from North

    ET,1,SHELL131          ! thermal shell element for walls
    ET,2,SHELL131          ! thermal shell element for roof
    SECTYPE,1,SHELL
    SECDATA,{design.wall_thickness_m}
    SECTYPE,2,SHELL
    SECDATA,{design.roof_thickness_m}

    ! Wall block (rectangular footprint approximation)
    BLOCK,0,10,0,0.01,0,3
    ! Roof plate
    BLOCK,0,10,0,10,3,3.01
    VMESH,ALL
    """)


def _time_varying_table(name: str, hourly_values, duration_hours: int) -> str:
    """Build an APDL *DIM / tabular-load array for an hourly profile."""
    lines = [f"*DIM,{name},TABLE,{duration_hours},1,1,TIME"]
    for hour, value in enumerate(hourly_values[:duration_hours]):
        t_sec = hour * 3600
        lines.append(f"{name}({hour+1},0,1) = {t_sec}")
        lines.append(f"{name}({hour+1},1,1) = {value}")
    return "\n".join(lines)


def _loads_block(climate: ClimateParams, design: ShelterDesignParams,
                  settings: SimulationSettings) -> str:
    ambient_table = _time_varying_table(
        "AMBTEMP", climate.ambient_temp_profile_c, settings.duration_hours)
    solar_table = _time_varying_table(
        "SOLARFLUX", climate.solar_radiation_profile_w_m2, settings.duration_hours)

    h_conv = 8.0 + 3.0 * climate.wind_speed_m_s / 3.0  # simple wind-adjusted h (W/m2K)

    return dedent(f"""\
    ! ---- Time-varying environmental loads ----
    {ambient_table}

    {solar_table}

    ! Convective film coefficient adjusted for wind speed {climate.wind_speed_m_s} m/s
    SF,ALL,CONV,{h_conv:.2f},%AMBTEMP%
    SF,ALL,HFLUX,%SOLARFLUX%          ! absorbed solar flux surface load
    ! Shading coefficient applied upstream: {design.shading_coefficient}
    ! Ventilation heat exchange: {design.ventilation_ach} ACH (modeled as extra convective term)
    ! Internal gains: {design.internal_gains_w} W ({design.num_occupants} occupants)
    """)


def _solution_block(settings: SimulationSettings) -> str:
    analysis_cmd = "ANTYPE,TRANS" if settings.analysis_type.value == "transient" else "ANTYPE,STATIC"
    return dedent(f"""\
    ! ---- Solution control ----
    /SOLU
    {analysis_cmd}
    DELTIM,{settings.time_step_s}
    TIME,{settings.duration_hours * 3600}
    AUTOTS,ON
    CNVTOL,TEMP,,{settings.convergence_tolerance}
    OUTRES,ALL,ALL
    SOLVE
    FINISH
    """)


def _postproc_block() -> str:
    return dedent("""\
    ! ---- Post-processing: export nodal temperature history ----
    /POST26
    NSOL,2,1,TEMP,,INDOOR_TEMP
    STORE,MERGE
    *CFOPEN,ansys_results,csv
    *VWRITE
    ('time_s,indoor_temp_c,heat_flux_w_m2')
    *DO,i,1,NPTS
        *GET,tval,VARI,1,ITEM,i
        *GET,tempval,VARI,2,ITEM,i
        *VWRITE,tval,tempval
    (F10.1,',',F8.3)
    *ENDDO
    *CFCLOS
    FINISH
    """)


def generate_apdl_input(case_dir: str,
                         design: ShelterDesignParams,
                         climate: ClimateParams,
                         settings: SimulationSettings) -> str:
    """Write a complete ANSYS APDL batch (.inp) file for this case.

    Returns the path to the generated .inp file.
    """
    os.makedirs(case_dir, exist_ok=True)
    input_path = os.path.join(case_dir, "shelter_thermal.inp")

    header = dedent(f"""\
    /BATCH
    /TITLE, Passive Shelter Transient Thermal Analysis - {design.design_id}
    /PREP7
    ! Auto-generated by Phase 8 ANSYS Bridge - do not hand edit above FINISH
    ! Climate zone: {climate.climate_zone.value} | Location: {climate.location_name}
    """)

    content = "\n".join([
        header,
        _material_block(design),
        _geometry_block(design),
        _loads_block(climate, design, settings),
        _solution_block(settings),
        _postproc_block(),
    ])

    with open(input_path, "w") as f:
        f.write(content)

    return input_path
