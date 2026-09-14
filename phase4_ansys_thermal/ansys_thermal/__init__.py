"""
ansys_thermal
=============

Phase 4 component of the SIH 2026 project:
"AI-Based Software Model for Designing Energy-Efficient Passive Shelters
for Different Climatic Conditions".

This package provides the ANSYS thermal simulation workflow and
automation layer. It is a completely independent component: it does not
require a frontend, a database, cloud deployment, or code from any other
phase.

Key design principle
---------------------
ANSYS installation, licensing, and available products differ between
systems, so this package cleanly separates:

    A. Simulation preparation   (ansys_thermal.models, .geometry)
    B. ANSYS execution adapter  (ansys_thermal.ansys.adapter / executor)
    C. Result extraction        (ansys_thermal.ansys.result_parser)
    D. Result normalization     (ansys_thermal.results.normalizer)

Two adapters are provided:

    - MockThermalAdapter: works on any machine, no ANSYS required.
      All outputs from this adapter are clearly labelled as MOCK and
      must never be presented as real ANSYS results.
    - AnsysThermalAdapter: contains the real integration points for an
      actual ANSYS installation (via pyansys / ANSYS APDL or Workbench
      scripting). If ANSYS is not available in the environment, it
      fails gracefully and instead produces ANSYS-ready input files
      that an engineer can run manually or via ANSYS batch mode.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
