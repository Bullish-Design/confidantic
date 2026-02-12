from __future__ import annotations

from typer.testing import CliRunner

from confidantic.cli import app


runner = CliRunner()


def test_cli_registers_expected_subapps() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "config" in result.stdout
    assert "schema" in result.stdout
    assert "workshop" in result.stdout
    assert "logs" in result.stdout


def test_legacy_top_level_commands_forward_to_config_commands() -> None:
    result_validate = runner.invoke(app, ["validate"])
    assert result_validate.exit_code == 0
    assert "validate: not yet implemented" in result_validate.stdout

    result_dump = runner.invoke(app, ["dump", "--format", "json"])
    assert result_dump.exit_code == 0
    assert result_dump.stdout.strip() == '{"format": "json", "status": "ok"}'

    result_fingerprint = runner.invoke(app, ["fingerprint"])
    assert result_fingerprint.exit_code == 0
    assert "fingerprint: unavailable" in result_fingerprint.stdout


def test_schema_and_logs_query_commands_exist() -> None:
    schema_help = runner.invoke(app, ["schema", "--help"])
    assert schema_help.exit_code == 0
    assert "export" in schema_help.stdout
    assert "vet" in schema_help.stdout

    logs_help = runner.invoke(app, ["logs", "--help"])
    assert logs_help.exit_code == 0
    assert "show" in logs_help.stdout
    assert "stats" in logs_help.stdout
    assert "query" in logs_help.stdout
