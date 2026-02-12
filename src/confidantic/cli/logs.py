"""Workshop log CLI commands."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import Enum

import typer

from confidantic.workshop.logging import WorkshopEvent, WorkshopLogReader

from .output import emit

app = typer.Typer(help="Workshop provenance log commands.", no_args_is_help=True)


class OutputFormat(str, Enum):
    """Output format options for log commands."""
    TEXT = "text"
    JSON = "json"
    JSONL = "jsonl"


def _parse_time(value: str | None) -> datetime | None:
    if value is None:
        return None
    normalized = value.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _parse_window(value: str | None) -> timedelta | None:
    if value is None:
        return None
    text = value.strip().lower()
    if text.endswith("ms"):
        return timedelta(milliseconds=float(text[:-2]))

    unit_map = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days"}
    if text[-1:] not in unit_map:
        raise ValueError("window must end with one of: ms, s, m, h, d")

    amount = float(text[:-1])
    return timedelta(**{unit_map[text[-1]]: amount})


def _serialize_events(events: list[WorkshopEvent]) -> list[dict[str, object]]:
    return [event.model_dump(mode="json") for event in events]


def _emit_events(ctx: typer.Context, events: list[WorkshopEvent], *, format: OutputFormat) -> None:
    if format == OutputFormat.JSONL:
        lines = [event.to_jsonl() for event in events]
        emit(ctx, payload={"count": len(events), "events": _serialize_events(events)}, text="\n".join(lines), quiet_text=str(len(events)))
        return

    if format == OutputFormat.JSON:
        emit(ctx, payload={"count": len(events), "events": _serialize_events(events)}, text=f"{len(events)} event(s)", quiet_text=str(len(events)))
        return

    lines = []
    for event in events:
        grammar = event.grammar or "-"
        duration = f" {event.duration_ms:.3f}ms" if event.duration_ms is not None else ""
        error = f" error={event.error}" if event.error else ""
        lines.append(
            f"{event.timestamp.isoformat().replace('+00:00', 'Z')} "
            f"{event.stage}/{event.status} grammar={grammar}{duration}{error}"
        )

    emit(
        ctx,
        payload={"count": len(events), "events": _serialize_events(events)},
        text="\n".join(lines),
        quiet_text=str(len(events)),
    )


@app.command("show")
def show(
    ctx: typer.Context,
    limit: int = typer.Option(20, "--limit", min=1, help="Max events to show."),
    grammar: str | None = typer.Option(None, "--grammar", help="Filter by grammar."),
    stage: str | None = typer.Option(None, "--stage", help="Filter by stage."),
    status: str | None = typer.Option(None, "--status", help="Filter by status."),
    failures_only: bool = typer.Option(False, "--failures-only", help="Show only failures."),
    format: OutputFormat = typer.Option(OutputFormat.TEXT, "--format", help="Output format."),
) -> None:
    """Show recent workshop log events with optional filters."""
    selected_status = "failure" if failures_only else status
    reader = WorkshopLogReader()
    events = reader.query_events(grammar=grammar, stage=stage, status=selected_status, limit=limit)
    _emit_events(ctx, events, format=format)


@app.command("stats")
def stats(
    ctx: typer.Context,
    format: OutputFormat = typer.Option(OutputFormat.TEXT, "--format", help="Output format."),
) -> None:
    """Show aggregate workshop log statistics."""
    reader = WorkshopLogReader()
    payload = reader.calculate_stats()

    if format in {OutputFormat.JSON, OutputFormat.JSONL}:
        emit(ctx, payload=payload, text="stats", quiet_text="ok")
        return

    lines = [f"total_events: {payload['total_events']}", f"failures: {payload['failures']}"]
    by_stage = payload.get("by_stage", {})
    avg_duration_ms = payload.get("avg_duration_ms", {})
    if by_stage:
        lines.append("by_stage:")
        for stage_name in sorted(by_stage):
            avg = avg_duration_ms.get(stage_name)
            avg_segment = f" avg_ms={avg}" if avg is not None else ""
            lines.append(f"  - {stage_name}: {by_stage[stage_name]}{avg_segment}")

    emit(ctx, payload=payload, text="\n".join(lines), quiet_text=str(payload["total_events"]))


@app.command("query")
def query(
    ctx: typer.Context,
    grammar: str | None = typer.Option(None, "--grammar", help="Filter by grammar."),
    stage: str | None = typer.Option(None, "--stage", help="Filter by stage."),
    status: str | None = typer.Option(None, "--status", help="Filter by status."),
    since: str | None = typer.Option(None, "--since", help="Inclusive lower timestamp bound (ISO-8601)."),
    until: str | None = typer.Option(None, "--until", help="Inclusive upper timestamp bound (ISO-8601)."),
    window: str | None = typer.Option(None, "--window", help="Relative time window ending now (e.g. 30m, 2h, 1d, 500ms)."),
    limit: int | None = typer.Option(None, "--limit", min=1, help="Optional max number of events."),
    format: OutputFormat = typer.Option(OutputFormat.TEXT, "--format", help="Output format."),
) -> None:
    """Query workshop events using explicit filtering predicates."""
    try:
        since_dt = _parse_time(since)
        until_dt = _parse_time(until)
        window_delta = _parse_window(window)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

    if window_delta is not None:
        since_dt = datetime.now(UTC) - window_delta

    if since_dt and until_dt and since_dt > until_dt:
        raise typer.BadParameter("--since must be before or equal to --until")

    reader = WorkshopLogReader()
    events = reader.query_events(
        grammar=grammar,
        stage=stage,
        status=status,
        since=since_dt,
        until=until_dt,
        limit=limit,
    )
    _emit_events(ctx, events, format=format)
