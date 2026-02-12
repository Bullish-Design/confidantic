"""Tests for JSONL workshop logging behavior."""

from __future__ import annotations

import json
from pathlib import Path

from confidantic.workshop.logging import WorkshopLogReader, WorkshopLogger


def test_jsonl_entries_are_valid_json(tmp_path: Path) -> None:
    log_file = tmp_path / "workshop.jsonl"
    logger = WorkshopLogger(log_path=log_file)

    logger.log_event(stage="load", status="success", grammar="python")
    logger.log_event(stage="generate", status="failure", grammar="python", error="synthetic")

    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert lines
    for line in lines:
        payload = json.loads(line)
        assert isinstance(payload, dict)


def test_jsonl_is_append_only(tmp_path: Path) -> None:
    log_file = tmp_path / "workshop.jsonl"
    logger = WorkshopLogger(log_path=log_file)

    logger.log_event(stage="load", status="success", grammar="python")
    first = log_file.read_text(encoding="utf-8")
    logger.log_event(stage="vet", status="success", grammar="python")
    second = log_file.read_text(encoding="utf-8")

    assert first in second
    assert len(second.splitlines()) == 2


def test_jsonl_reader_handles_invalid_lines_with_warning(tmp_path: Path) -> None:
    log_file = tmp_path / "workshop.jsonl"
    log_file.write_text('{"stage":"load","status":"success","timestamp":"2024-01-01T00:00:00Z"}\nnot-json\n', encoding="utf-8")
    events = WorkshopLogReader(log_path=log_file).read_all()
    assert len(events) == 1
