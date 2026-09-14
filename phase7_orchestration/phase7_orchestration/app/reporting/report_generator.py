"""Helpers for exporting an EngineeringReport to JSON and Markdown files."""
from pathlib import Path

from app.models.report import EngineeringReport


def report_to_json(report: EngineeringReport) -> str:
    return report.model_dump_json(indent=2)


def write_report_files(report: EngineeringReport, output_dir: str, basename: str = "report") -> tuple[str, str]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / f"{basename}.json"
    md_path = out / f"{basename}.md"

    json_path.write_text(report_to_json(report), encoding="utf-8")
    md_path.write_text(report.to_markdown(), encoding="utf-8")

    return str(json_path), str(md_path)
