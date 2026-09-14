"""Mock ANSYS validation adapter.

IMPORTANT: This does NOT run ANSYS or any real FEA/CFD solver. It produces
deterministic, clearly-labeled MOCK results so the orchestration layer and
downstream reporting can be built and tested against a stable interface.
A real implementation would submit a job to ANSYS (Mechanical/Fluent/etc.)
via its scripting or batch API and poll for completion.
"""
import hashlib

from app.interfaces.ansys import ANSYSValidator
from app.models.design import ShelterDesign
from app.models.results import ANSYSValidationResult


class MockANSYSValidator(ANSYSValidator):
    def __init__(self) -> None:
        self._jobs: dict[str, str] = {}

    def validate_design(self, design: ShelterDesign) -> str:
        job_id = f"mock-ansys-{design.design_id}"
        self._jobs[job_id] = design.design_id
        return job_id

    def get_validation_results(self, job_id: str, design: ShelterDesign) -> ANSYSValidationResult:
        # Deterministic pseudo-stress derived from geometry only, purely to
        # exercise the interface shape. Not a structural analysis.
        opening_ratio = design.opening_area_m2 / max(design.wall_area_m2, 1.0)
        digest = int(hashlib.sha256(design.design_id.encode()).hexdigest(), 16)
        base_stress = 5.0 + (digest % 100) / 20.0  # deterministic 5.0-10.0 MPa range
        predicted_stress = round(base_stress * (design.height_m / 2.7), 2)

        if opening_ratio > 0.3:
            risk = "high"
        elif opening_ratio > 0.15:
            risk = "medium"
        else:
            risk = "low"

        return ANSYSValidationResult(
            is_mock=True,
            design_id=design.design_id,
            validated=True,
            predicted_max_stress_mpa=predicted_stress,
            predicted_thermal_bridging_risk=risk,
            notes=(
                "MOCK VALIDATION ONLY. No ANSYS solver was executed. These figures are "
                "placeholder outputs used to exercise the ANSYSValidator interface and "
                "must not be used for any real engineering decision."
            ),
        )
