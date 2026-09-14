from app.interfaces.optimizer import DesignOptimizer


def test_mock_implements_interface(optimizer):
    assert isinstance(optimizer, DesignOptimizer)


def test_generate_candidates_returns_nonempty_unique_ids(optimizer, climate_provider, ladakh_request):
    climate = climate_provider.get_climate_profile(
        ladakh_request.location, ladakh_request.climate_description
    )
    candidates = optimizer.generate_candidates(ladakh_request, climate)
    assert len(candidates) > 0
    ids = [c.design_id for c in candidates]
    assert len(ids) == len(set(ids))


def test_generate_baseline_is_flagged(optimizer, climate_provider, ladakh_request):
    climate = climate_provider.get_climate_profile(
        ladakh_request.location, ladakh_request.climate_description
    )
    baseline = optimizer.generate_baseline(ladakh_request, climate)
    assert baseline.is_baseline is True
    assert baseline.insulation_thickness_m == 0.0
