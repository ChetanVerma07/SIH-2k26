import json
import tempfile
from pathlib import Path

from app.reporting.report_generator import report_to_json, write_report_files


def test_report_to_json_is_valid_json(orchestrator, ladakh_request):
    report = orchestrator.run_design_analysis(ladakh_request)
    text = report_to_json(report)
    parsed = json.loads(text)
    assert parsed["location"] == "Ladakh"
    assert "recommended_design" in parsed
    assert "confidence" in parsed


def test_report_to_markdown_contains_key_sections(orchestrator, ladakh_request):
    report = orchestrator.run_design_analysis(ladakh_request)
    md = report.to_markdown()

    for heading in [
        "## Project",
        "## Climate",
        "## Recommended Design",
        "## Performance",
        "## Baseline Comparison",
        "## Robustness",
        "## Confidence",
        "## Recommendation",
        "## Assumptions",
        "## Limitations",
    ]:
        assert heading in md


def test_markdown_flags_mock_status(orchestrator, ladakh_request):
    report = orchestrator.run_design_analysis(ladakh_request)
    md = report.to_markdown()
    assert "MOCK" in md


def test_write_report_files_creates_both_files(orchestrator, ladakh_request):
    report = orchestrator.run_design_analysis(ladakh_request)
    with tempfile.TemporaryDirectory() as tmp:
        json_path, md_path = write_report_files(report, tmp, basename="test_report")
        assert Path(json_path).exists()
        assert Path(md_path).exists()
        assert Path(json_path).read_text(encoding="utf-8")
        assert Path(md_path).read_text(encoding="utf-8")
