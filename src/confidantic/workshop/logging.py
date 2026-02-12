"""Append-only JSONL provenance logging for workshop workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Any, ClassVar, Literal
import warnings

import fcntl

Stage = Literal["load", "generate", "fmt", "vet", "test", "doctor"]
Status = Literal["started", "success", "failure"]


@dataclass(slots=True)
class WorkshopEvent:
    """Single workshop event encoded as one JSONL line."""

    model_fields: ClassVar[dict[str, Any]] = {
        "timestamp": datetime,
        "stage": str,
        "status": str,
        "grammar": str,
        "artifact_paths": list,
        "error": str,
        "duration_ms": float,
        "metadata": dict,
    }

    timestamp: datetime
    stage: Stage
    status: Status
    grammar: str | None = None
    artifact_paths: list[str] = field(default_factory=list)
    error: str | None = None
    duration_ms: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    agent_id: str | None = None
    session_id: str | None = None
    user_id: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))
        self.timestamp = self.timestamp.astimezone(timezone.utc)

    def model_dump(self, mode: str = "python") -> dict[str, Any]:
        payload = {
            "timestamp": self.timestamp,
            "stage": self.stage,
            "status": self.status,
            "grammar": self.grammar,
            "artifact_paths": list(self.artifact_paths),
            "error": self.error,
            "duration_ms": self.duration_ms,
            "metadata": dict(self.metadata),
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
        }
        if mode == "json":
            payload["timestamp"] = self.timestamp.isoformat().replace("+00:00", "Z")
        return {k: v for k, v in payload.items() if v is not None}

    def model_dump_json(self) -> str:
        return json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))

    def to_jsonl(self) -> str:
        return self.model_dump_json()

    @classmethod
    def from_jsonl(cls, line: str) -> "WorkshopEvent":
        return cls(**json.loads(line))


class WorkshopLogger:
    """File-lock protected JSONL logger for workshop activity."""

    def __init__(self, log_path: Path = Path("logs/workshop.jsonl")):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def _safe_append(self, line: str) -> None:
        with self.log_path.open("a", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                handle.write(line)
                handle.write("\n")
                handle.flush()
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def log_event(
        self,
        *,
        stage: Stage,
        status: Status,
        grammar: str | None = None,
        artifact_paths: list[Path] | None = None,
        error: str | None = None,
        metadata: dict[str, Any] | None = None,
        duration_ms: float | None = None,
    ) -> None:
        event = WorkshopEvent(
            timestamp=datetime.now(timezone.utc),
            stage=stage,
            status=status,
            grammar=grammar,
            artifact_paths=[str(path) for path in (artifact_paths or [])],
            error=error,
            metadata=metadata or {},
            duration_ms=duration_ms,
        )
        try:
            self._safe_append(event.to_jsonl())
        except OSError as exc:
            warnings.warn(f"Failed writing workshop log at {self.log_path}: {exc}", stacklevel=2)

    def log_stage_start(self, stage: Stage, grammar: str) -> float:
        started = time.perf_counter()
        self.log_event(stage=stage, status="started", grammar=grammar)
        return started

    def log_stage_end(
        self,
        stage: Stage,
        grammar: str,
        start_time: float,
        success: bool,
        error: str | None = None,
        artifact_paths: list[Path] | None = None,
    ) -> None:
        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 3)
        self.log_event(
            stage=stage,
            status="success" if success else "failure",
            grammar=grammar,
            error=error,
            duration_ms=duration_ms,
            artifact_paths=artifact_paths,
        )


class WorkshopLogReader:
    """Query and summarize workshop JSONL logs."""

    def __init__(self, log_path: Path = Path("logs/workshop.jsonl")):
        self.log_path = Path(log_path)

    def read_all(self) -> list[WorkshopEvent]:
        if not self.log_path.exists():
            return []

        events: list[WorkshopEvent] = []
        with self.log_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                text = line.strip()
                if not text:
                    continue
                try:
                    events.append(WorkshopEvent.from_jsonl(text))
                except Exception as exc:
                    warnings.warn(
                        f"Skipping invalid workshop JSONL line {line_number} in {self.log_path}: {exc}",
                        stacklevel=2,
                    )
        return events

    def filter_by_grammar(self, grammar: str) -> list[WorkshopEvent]:
        return [event for event in self.read_all() if event.grammar == grammar]

    def filter_by_stage(self, stage: str) -> list[WorkshopEvent]:
        return [event for event in self.read_all() if event.stage == stage]

    def filter_by_status(self, status: str) -> list[WorkshopEvent]:
        return [event for event in self.read_all() if event.status == status]

    def get_failures(self) -> list[WorkshopEvent]:
        return self.filter_by_status("failure")

    def get_recent(self, limit: int = 10) -> list[WorkshopEvent]:
        events = sorted(self.read_all(), key=lambda event: event.timestamp)
        return events[-limit:]

    def query_events(
        self,
        *,
        grammar: str | None = None,
        stage: str | None = None,
        status: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int | None = None,
    ) -> list[WorkshopEvent]:
        """Return events matching explicit filter predicates."""
        events = sorted(self.read_all(), key=lambda event: event.timestamp)
        if grammar is not None:
            events = [event for event in events if event.grammar == grammar]
        if stage is not None:
            events = [event for event in events if event.stage == stage]
        if status is not None:
            events = [event for event in events if event.status == status]
        if since is not None:
            events = [event for event in events if event.timestamp >= since]
        if until is not None:
            events = [event for event in events if event.timestamp <= until]
        if limit is not None:
            events = events[-limit:]
        return events

    def calculate_stats(self) -> dict[str, Any]:
        events = self.read_all()
        by_stage: dict[str, list[float]] = {}
        for event in events:
            if event.duration_ms is None:
                continue
            by_stage.setdefault(event.stage, []).append(event.duration_ms)

        avg_duration_ms = {
            stage: round(sum(values) / len(values), 3)
            for stage, values in sorted(by_stage.items())
            if values
        }

        return {
            "total_events": len(events),
            "failures": sum(1 for event in events if event.status == "failure"),
            "by_stage": {stage: len(self.filter_by_stage(stage)) for stage in sorted({e.stage for e in events})},
            "avg_duration_ms": avg_duration_ms,
        }
