"""Transparent confidence assessment.

None of the figures below are random. Each is a documented function of
concrete factors so a reviewer can audit exactly how it was derived.
"""
from app.models.climate import ClimateProfile
from app.models.results import ConfidenceAssessment, RobustnessSummary, ANSYSValidationResult

MAX_EXPECTED_MISSING_FIELDS = 4  # used to normalize the data-completeness penalty


def assess_confidence(
    climate: ClimateProfile,
    robustness: RobustnessSummary,
    ansys_result: ANSYSValidationResult | None,
) -> ConfidenceAssessment:
    # --- Data confidence ---
    # Penalize missing/estimated climate fields (normalized against an
    # expected baseline count), scaled by how dense the underlying data
    # points are relative to a full 24-point daily profile.
    missing_penalty = min(
        len(climate.missing_fields) / MAX_EXPECTED_MISSING_FIELDS, 1.0
    ) * 40.0
    density_factor = 0.6 + 0.4 * min(climate.data_points_available / 24.0, 1.0)
    data_confidence = round(max(0.0, 100.0 - missing_penalty) * density_factor, 1)

    # --- Simulation confidence ---
    # More scenarios evaluated => more evidence the result generalizes.
    scenario_bonus = min(robustness.scenarios_evaluated * 8.0, 40.0)
    ansys_bonus = 15.0 if (ansys_result is not None and ansys_result.validated) else 0.0
    simulation_confidence = round(min(100.0, 45.0 + scenario_bonus + ansys_bonus), 1)

    # --- Recommendation confidence ---
    # Combines data and simulation confidence, tempered by how consistent
    # performance was across scenarios (robustness score) rather than a
    # single favorable run.
    recommendation_confidence = round(
        (0.35 * data_confidence + 0.35 * simulation_confidence + 0.30 * robustness.robustness_score),
        1,
    )

    explanation = (
        f"Data confidence reflects {len(climate.missing_fields)} missing/estimated climate "
        f"field(s) out of an expected baseline of {MAX_EXPECTED_MISSING_FIELDS}, and "
        f"{climate.data_points_available} available data point(s). Simulation confidence "
        f"reflects {robustness.scenarios_evaluated} scenario(s) evaluated"
        + (" plus mock ANSYS validation" if ansys_bonus else " with no ANSYS validation performed")
        + f". Recommendation confidence combines both with the robustness score "
        f"({robustness.robustness_score:.1f}/100), so a design that only performs well in one "
        f"scenario does not receive high confidence."
    )

    return ConfidenceAssessment(
        data_confidence=data_confidence,
        simulation_confidence=simulation_confidence,
        recommendation_confidence=recommendation_confidence,
        explanation=explanation,
    )
