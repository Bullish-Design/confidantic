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


def test_doctor_reports_cue_vet_output_details(tmp_path: Path, monkeypatch) -> None:
    schemas_dir = tmp_path / "build" / "schemas" / "cue" / "python"
    schemas_dir.mkdir(parents=True, exist_ok=True)
    for name in ("captures.cue", "metadata.cue", "node_types.cue"):
        (schemas_dir / name).write_text("package python\n", encoding="utf-8")

    calls: dict[str, Path] = {}

    def _fake_vet(path: Path, schema: Path | None = None, *, cwd: Path | None = None):
        calls["path"] = path
        calls["cwd"] = cwd
        raise RuntimeError("stdout: bad\nstderr: package mismatch")

    monkeypatch.setattr("confidantic.workshop.doctor.run_cue_vet", _fake_vet)

    doctor = WorkshopDoctor(
        grammar="python",
        node_types_path=FIXTURES / "node-types.json",
        queries_dir=FIXTURES / "queries",
        schemas_dir=schemas_dir,
    )

    report = doctor.run_diagnostics()
    cue_errors = [issue for issue in report.errors if issue.category == "cue_validity"]
    assert cue_errors
    assert "stdout: bad" in cue_errors[0].message
    assert calls["path"] == Path("python")
    assert calls["cwd"] == schemas_dir.parent


def test_doctor_reports_incomplete_generated_schema_set(tmp_path: Path) -> None:
    schemas_dir = tmp_path / "build" / "schemas" / "cue" / "python"
    schemas_dir.mkdir(parents=True, exist_ok=True)
    (schemas_dir / "captures.cue").write_text("package python\n", encoding="utf-8")

    doctor = WorkshopDoctor(
        grammar="python",
        node_types_path=FIXTURES / "node-types.json",
        queries_dir=FIXTURES / "queries",
        schemas_dir=schemas_dir,
    )
    report = doctor.run_diagnostics()

    assert any(
        issue.category == "cue_validity" and "incomplete" in issue.message
        for issue in report.errors
    )


def test_doctor_reports_package_mismatch(tmp_path: Path, monkeypatch) -> None:
    schemas_dir = tmp_path / "build" / "schemas" / "cue" / "python"
    schemas_dir.mkdir(parents=True, exist_ok=True)
    (schemas_dir / "captures.cue").write_text("package python\n", encoding="utf-8")
    (schemas_dir / "metadata.cue").write_text("package rust\n", encoding="utf-8")
    (schemas_dir / "node_types.cue").write_text("package python\n", encoding="utf-8")

    monkeypatch.setattr("confidantic.workshop.doctor.run_cue_vet", lambda *args, **kwargs: None)

    doctor = WorkshopDoctor(
        grammar="python",
        node_types_path=FIXTURES / "node-types.json",
        queries_dir=FIXTURES / "queries",
        schemas_dir=schemas_dir,
    )
    report = doctor.run_diagnostics()

    assert any(
        issue.category == "cue_validity" and "mismatched package" in issue.message
        for issue in report.errors
    )
