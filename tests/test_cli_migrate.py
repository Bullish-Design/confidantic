from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from confidantic.cli import app


runner = CliRunner()


def test_migrate_check_reports_deprecated_patterns() -> None:
    with runner.isolated_filesystem():
        config_path = Path("confidantic.toml")
        config_path.write_text('config_root = ".devman/.config"\nprofile = "default"\n', encoding="utf-8")

        result = runner.invoke(app, ["migrate", "check", "--path", str(config_path)])

        assert result.exit_code == 2
        payload = json.loads(result.stdout)
        assert payload["status"] == "deprecated-patterns-found"
        assert len(payload["findings"]) == 2
        assert {finding["replacement"] for finding in payload["findings"]} == {"root =", "profile_default ="}


def test_migrate_apply_rewrites_and_creates_backup() -> None:
    with runner.isolated_filesystem():
        config_path = Path("confidantic.toml")
        config_path.write_text('data_file = "records.jsonl"\n', encoding="utf-8")

        result = runner.invoke(app, ["migrate", "apply", "--path", str(config_path)])

        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["status"] == "migrated"
        assert payload["replacements"] == 1
        assert payload["changed_files"] == [str(config_path)]
        assert payload["backup"] == "confidantic.toml.bak"
        assert Path("confidantic.toml.bak").exists()
        assert "data_files" in config_path.read_text(encoding="utf-8")


def test_migrate_doctor_aggregates_project_findings() -> None:
    with runner.isolated_filesystem():
        Path("profiles").mkdir(parents=True, exist_ok=True)
        Path("profiles/default.toml").write_text('profile = "default"\n', encoding="utf-8")

        result = runner.invoke(app, ["migrate", "doctor", "--root", "."])

        assert result.exit_code == 2
        payload = json.loads(result.stdout)
        assert payload["status"] == "deprecated-patterns-found"
        assert payload["total_findings"] == 1
        assert any(path.endswith("profiles/default.toml") for path in payload["files_with_findings"])


def test_migrate_check_exits_zero_when_no_deprecated_patterns() -> None:
    with runner.isolated_filesystem():
        config_path = Path("confidantic.toml")
        config_path.write_text('root = ".devman/.config"\nprofile_default = "default"\n', encoding="utf-8")

        result = runner.invoke(app, ["migrate", "check", "--path", str(config_path)])

        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["status"] == "ok"
        assert payload["findings"] == []


def test_migrate_doctor_scans_confidantic_and_profiles() -> None:
    with runner.isolated_filesystem():
        Path("profiles").mkdir(parents=True, exist_ok=True)
        Path("confidantic.toml").write_text('config_root = ".devman/.config"\n', encoding="utf-8")
        Path("profiles/default.toml").write_text('profile = "default"\n', encoding="utf-8")

        result = runner.invoke(app, ["migrate", "doctor", "--root", "."])

        assert result.exit_code == 2
        payload = json.loads(result.stdout)
        assert payload["status"] == "deprecated-patterns-found"
        assert payload["total_findings"] == 2
        assert any(path.endswith("confidantic.toml") for path in payload["files_with_findings"])
        assert any(path.endswith("profiles/default.toml") for path in payload["files_with_findings"])
