from __future__ import annotations

import json
from pathlib import Path

from confidantic.workshop.doctor import (
    WorkshopDoctor,
    export_diagnostic_report,
    format_diagnostic_report,
)


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "python"


def test_doctor_reports_missing_artifacts(tmp_path: Path) -> None:
    doctor = WorkshopDoctor(
        grammar="python",
        node_types_path=tmp_path / "missing-node-types.json",
        queries_dir=tmp_path / "missing-queries",
    )
    report = doctor.run_diagnostics()
    assert not report.is_healthy()
    assert any(issue.category == "missing_artifact" for issue in report.errors)


def test_doctor_valid_inputs_include_info_section() -> None:
    doctor = WorkshopDoctor(
        grammar="python",
        node_types_path=FIXTURES / "node-types.json",
        queries_dir=FIXTURES / "queries",
    )
    report = doctor.run_diagnostics()
    assert report.checks_run >= 6
    assert format_diagnostic_report(report)


def test_export_diagnostic_report_json_and_markdown(tmp_path: Path) -> None:
    doctor = WorkshopDoctor(
        grammar="python",
        node_types_path=FIXTURES / "node-types.json",
        queries_dir=FIXTURES / "queries",
    )
    report = doctor.run_diagnostics()

    json_path = tmp_path / "doctor.json"
    md_path = tmp_path / "doctor.md"

    export_diagnostic_report(report, json_path, format="json")
    export_diagnostic_report(report, md_path, format="markdown")

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["grammar"] == "python"
    assert md_path.read_text(encoding="utf-8").startswith("# Workshop diagnostics")
