from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from confidantic.cli import app
from confidantic.workshop.logging import WorkshopLogger


def test_logs_show_and_stats_commands(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    logger = WorkshopLogger(Path("logs/workshop.jsonl"))
    logger.log_event(stage="doctor", status="failure", grammar="python", error="bad")

    runner = CliRunner()
    show_result = runner.invoke(app, ["logs", "show", "--failures-only"])
    assert show_result.exit_code == 0
    assert '"status":"failure"' in show_result.stdout

    stats_result = runner.invoke(app, ["logs", "stats"])
    assert stats_result.exit_code == 0
    payload = json.loads(stats_result.stdout)
    assert payload["failures"] == 1
