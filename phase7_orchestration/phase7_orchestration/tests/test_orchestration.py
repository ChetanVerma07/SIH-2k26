from app.models.report import EngineeringReport


def test_full_workflow_returns_engineering_report(orchestrator, ladakh_request):
    report = orchestrator.run_design_analysis(ladakh_request)
    assert isinstance(report, EngineeringReport)
    assert report.location == "Ladakh"
    assert report.recommended_design.design_id != report.baseline_design.design_id


def test_workflow_raises_on_invalid_comfort_range(orchestrator, ladakh_request):
    import pytest
    from app.models.request import ComfortRange

    # Bypass field validation (which already rejects this at construction time)
    # to confirm the orchestrator's own defensive check also catches it.
    bad_request = ladakh_request.model_copy(deep=True)
    bad_request.comfort_range = ComfortRange.model_construct(min_c=26, max_c=18)

    with pytest.raises(ValueError):
        orchestrator.run_design_analysis(bad_request)


def test_baseline_comparison_reflects_actual_numbers(orchestrator, ladakh_request):
    report = orchestrator.run_design_analysis(ladakh_request)
    c = report.comparison

    assert c.baseline_heat_loss_kwh == report.baseline_results.total_heat_loss_kwh
    assert c.optimized_heat_loss_kwh == report.results.total_heat_loss_kwh
    expected_pct = round(
        (c.baseline_heat_loss_kwh - c.optimized_heat_loss_kwh) / c.baseline_heat_loss_kwh * 100, 2
    )
    assert c.heat_loss_improvement_percent == expected_pct


def test_recommended_design_scores_at_least_as_well_as_all_candidates(orchestrator, ladakh_request):
    report = orchestrator.run_design_analysis(ladakh_request)
    candidates = orchestrator._optimizer.generate_candidates(ladakh_request, report.climate)
    for c in candidates:
        perf = orchestrator._thermal_simulator.simulate(
            c, report.climate, ladakh_request.comfort_range, ladakh_request.simulation_duration_hours
        )
        assert report.results.overall_score >= perf.overall_score
