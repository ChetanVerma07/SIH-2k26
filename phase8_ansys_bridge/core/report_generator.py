"""
Phase 8 - Structured validation report generator.

Produces both a machine-readable report.json (for chaining into any later
phase / dashboard) and a human-readable report.md summarizing the whole
run: design + climate inputs, ANSYS results, simplified-model results,
their comparison, and the final validation verdict.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from config import ShelterDesignParams, ClimateParams, SimulationSettings
from core.metrics_extractor import ThermalMetrics
from core.comparator import ComparisonReport
from core.validator import ValidationReport


def _fmt_table(headers, rows) -> str:
    line = "| " + " | ".join(headers) + " |"
    sep = "|" + "|".join(["---"] * len(headers)) + "|"
    body = "\n".join("| " + " | ".join(str(c) for c in row) + " |" for row in rows)
    return "\n".join([line, sep, body])


def generate_report(case_dir: str,
                     case_id: str,
                     design: ShelterDesignParams,
                     climate: ClimateParams,
                     settings: SimulationSettings,
                     backend_name: str,
                     ansys_metrics: ThermalMetrics,
                     simplified_metrics: ThermalMetrics,
                     comparison: ComparisonReport,
                     validation: ValidationReport) -> dict:
    """Writes report.json and report.md into case_dir. Returns the JSON dict."""

    report = {
        "case_id": case_id,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "backend_used": backend_name,
        "design": design.to_dict(),
        "climate": climate.to_dict(),
        "settings": settings.to_dict(),
        "ansys_metrics": ansys_metrics.to_dict(),
        "simplified_model_metrics": simplified_metrics.to_dict(),
        "comparison": comparison.to_dict(),
        "validation": validation.to_dict(),
    }

    json_path = os.path.join(case_dir, "report.json")
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)

    md_path = os.path.join(case_dir, "report.md")
    with open(md_path, "w") as f:
        f.write(_render_markdown(report))

    return report


def _render_markdown(report: dict) -> str:
    d = report["design"]
    c = report["climate"]
    s = report["settings"]
    am = report["ansys_metrics"]
    sm = report["simplified_model_metrics"]
    comp = report["comparison"]
    val = report["validation"]

    lines = []
    lines.append(f"# Phase 8 Validation Report -- {report['case_id']}")
    lines.append(f"_Generated: {report['generated_utc']}_")
    lines.append(f"\n**Backend used:** `{report['backend_used']}`  ")
    lines.append(f"**Overall verdict:** **{val['overall_verdict'].upper()}**\n")

    lines.append("## 1. Shelter Design Parameters")
    lines.append(_fmt_table(
        ["Parameter", "Value"],
        [(k, v) for k, v in d.items()],
    ))

    lines.append("\n## 2. Climate Parameters")
    climate_rows = [(k, v) for k, v in c.items()
                     if k not in ("ambient_temp_profile_c", "solar_radiation_profile_w_m2")]
    lines.append(_fmt_table(["Parameter", "Value"], climate_rows))

    lines.append("\n## 3. Simulation Settings")
    lines.append(_fmt_table(["Setting", "Value"], [(k, v) for k, v in s.items()]))

    lines.append("\n## 4. ANSYS (Backend) Thermal Metrics")
    lines.append(_fmt_table(["Metric", "Value"], [(k, v) for k, v in am.items()]))

    lines.append("\n## 5. Simplified Model Thermal Metrics")
    lines.append(_fmt_table(["Metric", "Value"], [(k, v) for k, v in sm.items()]))

    lines.append("\n## 6. ANSYS vs Simplified Model Comparison")
    comp_rows = [(m["metric"], m["ansys_value"], m["simplified_value"],
                  m["pct_diff"], "OK" if m["within_tolerance"] else "OUT OF TOLERANCE")
                 for m in comp["metric_comparisons"]]
    lines.append(_fmt_table(
        ["Metric", "ANSYS", "Simplified", "% Diff", "Status"], comp_rows))
    lines.append(f"\nIndoor-temperature RMSE: **{comp['rmse_indoor_temp_c']} C** | "
                 f"Correlation: **{comp['correlation_indoor_temp']}** | "
                 f"Overall within tolerance: **{comp['overall_within_tolerance']}**")

    lines.append("\n## 7. Design Validation")
    val_rows = [(r["rule"], r["verdict"].upper(), r["detail"]) for r in val["rules"]]
    lines.append(_fmt_table(["Rule", "Verdict", "Detail"], val_rows))

    lines.append(f"\n## 8. Conclusion\n")
    lines.append(_conclusion_text(val["overall_verdict"]))

    return "\n".join(lines) + "\n"


def _conclusion_text(overall_verdict: str) -> str:
    if overall_verdict == "pass":
        return ("The design meets expected passive-thermal-performance behaviour "
                "for its climate zone, and the ANSYS run agrees with the "
                "independent simplified model within tolerance. The design can "
                "proceed to detailed drawings / prototyping.")
    if overall_verdict == "warning":
        return ("The design is broadly workable but one or more checks are "
                "borderline (see table above). Review the flagged rule(s) -- "
                "typically thermal mass, insulation level, or shading -- before "
                "finalizing.")
    return ("The design does NOT currently meet expected passive-thermal "
            "performance for its climate zone, or the ANSYS/simplified-model "
            "results disagree beyond tolerance. Revisit envelope material, "
            "insulation, shading, or ventilation assumptions and re-run.")
