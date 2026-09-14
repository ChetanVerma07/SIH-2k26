from app.services.recommendation import generate_recommendation


def test_recommendation_headline_uses_actual_metrics(orchestrator, ladakh_request):
    report = orchestrator.run_design_analysis(ladakh_request)
    rec = report.recommendation

    assert f"{report.results.comfort_percentage:.0f}%" in rec.headline
    assert f"{report.comparison.heat_loss_improvement_percent:.0f}%" in rec.headline


def test_recommendation_has_reasons_and_tradeoffs(orchestrator, ladakh_request):
    report = orchestrator.run_design_analysis(ladakh_request)
    rec = report.recommendation

    assert len(rec.reasons) >= 3
    assert len(rec.tradeoffs) >= 1


def test_recommendation_reasons_reference_robustness(orchestrator, ladakh_request):
    report = orchestrator.run_design_analysis(ladakh_request)
    rec = report.recommendation

    assert any("Robustness" in reason for reason in rec.reasons)
