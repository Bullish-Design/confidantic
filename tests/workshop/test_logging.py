from __future__ import annotations

import threading
from pathlib import Path

from confidantic.workshop.logging import WorkshopLogReader, WorkshopLogger


def test_workshop_logger_round_trip(tmp_path: Path) -> None:
    log_path = tmp_path / "workshop.jsonl"
    logger = WorkshopLogger(log_path)
    start = logger.log_stage_start("load", "python")
    logger.log_stage_end("load", "python", start, success=True)

    reader = WorkshopLogReader(log_path)
    events = reader.read_all()
    assert len(events) == 2
    assert events[0].status == "started"
    assert events[1].status == "success"


def test_workshop_logger_concurrent_writes(tmp_path: Path) -> None:
    log_path = tmp_path / "workshop.jsonl"
    logger = WorkshopLogger(log_path)

    def worker(idx: int) -> None:
        logger.log_event(stage="generate", status="success", grammar=f"g{idx}")

    threads = [threading.Thread(target=worker, args=(idx,)) for idx in range(20)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    reader = WorkshopLogReader(log_path)
    assert len(reader.read_all()) == 20


def test_log_reader_stats(tmp_path: Path) -> None:
    log_path = tmp_path / "workshop.jsonl"
    logger = WorkshopLogger(log_path)
    logger.log_event(stage="load", status="success", grammar="python", duration_ms=10)
    logger.log_event(stage="load", status="failure", grammar="python", duration_ms=20, error="boom")

    stats = WorkshopLogReader(log_path).calculate_stats()
    assert stats["total_events"] == 2
    assert stats["failures"] == 1
    assert stats["avg_duration_ms"]["load"] == 15.0
