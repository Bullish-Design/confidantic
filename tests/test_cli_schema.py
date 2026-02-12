from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from confidantic.cli import app
from confidantic.workshop.services import WorkshopGenerateResult, WorkshopValidateResult


def test_schema_export_command_emits_machine_parseable_success(monkeypatch, tmp_path: Path) -> None:
    output_dir = tmp_path / "schemas"
    generated = (output_dir / "captures.cue", output_dir / "metadata.cue")

    def fake_generate_workshop_schemas(*, grammar: str, node_types_path: Path, queries_dir: Path, output_dir: Path):
        assert grammar == "python"
        assert node_types_path == tmp_path / "node-types.json"
        assert queries_dir == tmp_path / "queries"
        assert output_dir == tmp_path / "schemas"
        return WorkshopGenerateResult(generated_files=generated)

    monkeypatch.setattr("confidantic.cli.schema.generate_workshop_schemas", fake_generate_workshop_schemas)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "schema",
            "export",
            "--grammar",
            "python",
            "--node-types",
            str(tmp_path / "node-types.json"),
            "--queries-dir",
            str(tmp_path / "queries"),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["command"] == "schema export"
    assert payload["generated_files"] == [str(path) for path in generated]


def test_schema_vet_command_emits_machine_parseable_failure(monkeypatch, tmp_path: Path) -> None:
    def fake_validate_workshop_output(*, output_dir: Path, grammar: str | None = None):
        assert grammar == "python"
        assert output_dir == tmp_path / "schemas"
        return WorkshopValidateResult(ok=False, errors=("vet failed",))

    monkeypatch.setattr("confidantic.cli.schema.validate_workshop_output", fake_validate_workshop_output)

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["schema", "vet", "--grammar", "python", "--output-dir", str(tmp_path / "schemas")],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stderr)
    assert payload["ok"] is False
    assert payload["status"] == "error"
    assert payload["message"] == "schema vet failed"
    assert payload["command"] == "schema vet"
    assert payload["grammar"] == "python"
    assert payload["output_dir"] == str(tmp_path / "schemas")
    assert payload["errors"] == ["vet failed"]


def test_schema_vet_command_emits_machine_parseable_success(monkeypatch, tmp_path: Path) -> None:
    def fake_validate_workshop_output(*, output_dir: Path, grammar: str | None = None):
        assert grammar == "python"
        assert output_dir == tmp_path / "schemas"
        return WorkshopValidateResult(ok=True, errors=())

    monkeypatch.setattr("confidantic.cli.schema.validate_workshop_output", fake_validate_workshop_output)

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["schema", "vet", "--grammar", "python", "--output-dir", str(tmp_path / "schemas")],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["status"] == "ok"
    assert payload["command"] == "schema vet"
    assert payload["grammar"] == "python"
    assert payload["output_dir"] == str(tmp_path / "schemas")


def test_schema_vet_command_exception_emits_machine_parseable_failure(monkeypatch, tmp_path: Path) -> None:
    def fake_validate_workshop_output(*, output_dir: Path, grammar: str | None = None):
        raise RuntimeError("cue vet crashed")

    monkeypatch.setattr("confidantic.cli.schema.validate_workshop_output", fake_validate_workshop_output)

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["schema", "vet", "--grammar", "python", "--output-dir", str(tmp_path / "schemas")],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stderr)
    assert payload["ok"] is False
    assert payload["status"] == "error"
    assert payload["command"] == "schema vet"
    assert payload["message"] == "schema vet failed: cue vet crashed"
    assert payload["errors"] == ["cue vet crashed"]
    assert payload["grammar"] == "python"
    assert payload["output_dir"] == str(tmp_path / "schemas")
