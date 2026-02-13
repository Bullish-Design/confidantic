from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from confidantic.cli import app
from confidantic.workshop.logging import WorkshopLogger

# CLI convention: Typer-native parameter validation errors are asserted from stderr.
# Structured confidantic application failures may still emit JSON payloads to stderr.


def test_logs_show_and_stats_commands(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    logger = WorkshopLogger(Path("logs/workshop.jsonl"))
    logger.log_event(stage="doctor", status="failure", grammar="python", error="bad")
    logger.log_event(stage="fmt", status="success", grammar="python", duration_ms=12.5)

    runner = CliRunner()
    show_result = runner.invoke(app, ["logs", "show", "--failures-only"])
    assert show_result.exit_code == 0
    assert "doctor/failure" in show_result.stdout

    show_json = runner.invoke(app, ["logs", "show", "--json"])
    assert show_json.exit_code == 0
    show_payload = json.loads(show_json.stdout)
    assert show_payload["count"] == 2
    assert show_payload["events"][0]["grammar"] == "python"
    assert "event(s)" not in show_json.stdout

    show_format_json = runner.invoke(app, ["logs", "show", "--format", "json"])
    assert show_format_json.exit_code == 0
    show_format_payload = json.loads(show_format_json.stdout)
    assert show_format_payload["count"] == 2
    assert "event(s)" not in show_format_json.stdout

    stats_result = runner.invoke(app, ["logs", "stats", "--format", "json"])
    assert stats_result.exit_code == 0
    payload = json.loads(stats_result.stdout)
    assert payload["failures"] == 1
    assert payload["by_stage"]["doctor"] == 1


def test_logs_query_filters_time_and_status(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    log_path = Path("logs/workshop.jsonl")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        "\n".join(
            [
                '{"timestamp":"2024-01-01T00:00:00Z","stage":"generate","status":"success","grammar":"python"}',
                '{"timestamp":"2024-01-02T00:00:00Z","stage":"vet","status":"failure","grammar":"python","error":"boom"}',
                '{"timestamp":"2024-01-03T00:00:00Z","stage":"vet","status":"success","grammar":"rust"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "logs",
            "query",
            "--grammar",
            "python",
            "--stage",
            "vet",
            "--status",
            "failure",
            "--since",
            "2024-01-01T12:00:00Z",
            "--until",
            "2024-01-02T12:00:00Z",
            "--json",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["count"] == 1
    assert payload["events"][0]["error"] == "boom"
    assert "event(s)" not in result.stdout

    format_json_result = runner.invoke(
        app,
        [
            "logs",
            "query",
            "--grammar",
            "python",
            "--stage",
            "vet",
            "--status",
            "failure",
            "--since",
            "2024-01-01T12:00:00Z",
            "--until",
            "2024-01-02T12:00:00Z",
            "--format",
            "json",
        ],
    )
    assert format_json_result.exit_code == 0
    format_payload = json.loads(format_json_result.stdout)
    assert format_payload["count"] == 1
    assert "event(s)" not in format_json_result.stdout

    bad_window = runner.invoke(app, ["logs", "query", "--window", "today"])
    assert bad_window.exit_code != 0
    assert "window must end with one of" in bad_window.stderr
