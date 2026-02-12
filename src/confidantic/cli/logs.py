"""Workshop log CLI commands."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
from typing import Literal

import typer

from confidantic.workshop.logging import WorkshopEvent, WorkshopLogReader

app = typer.Typer(help="Workshop provenance log commands.", no_args_is_help=True)


OutputFormat = Literal["text", "json", "jsonl"]


def _resolve_format(format: OutputFormat, json_output: bool) -> OutputFormat:
    return "json" if json_output else format


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

    unit_map = {
        "s": "seconds",
        "m": "minutes",
        "h": "hours",
        "d": "days",
    }
    if text[-1:] not in unit_map:
        raise ValueError("window must end with one of: ms, s, m, h, d")

    amount = float(text[:-1])
    return timedelta(**{unit_map[text[-1]]: amount})


def _serialize_events(events: list[WorkshopEvent]) -> list[dict[str, object]]:
    return [event.model_dump(mode="json") for event in events]


def _emit_events(events: list[WorkshopEvent], *, format: OutputFormat) -> None:
    if format == "json":
        payload = {"count": len(events), "events": _serialize_events(events)}
        typer.echo(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        return
    if format == "jsonl":
        for event in events:
            typer.echo(event.to_jsonl())
        return

    for event in events:
        grammar = event.grammar or "-"
        duration = f" {event.duration_ms:.3f}ms" if event.duration_ms is not None else ""
        error = f" error={event.error}" if event.error else ""
        typer.echo(
            f"{event.timestamp.isoformat().replace('+00:00', 'Z')} "
            f"{event.stage}/{event.status} grammar={grammar}{duration}{error}"
        )


@app.command("show")
def show(
    limit: int = typer.Option(20, "--limit", min=1, help="Max events to show."),
    grammar: str | None = typer.Option(None, "--grammar", help="Filter by grammar."),
    stage: str | None = typer.Option(None, "--stage", help="Filter by stage."),
    status: str | None = typer.Option(None, "--status", help="Filter by status."),
    failures_only: bool = typer.Option(False, "--failures-only", help="Show only failures."),
    format: OutputFormat = typer.Option("text", "--format", help="Output format."),
    json_output: bool = typer.Option(False, "--json", help="Shortcut for --format json."),
) -> None:
    """Show recent workshop log events with optional filters."""
    selected_status = "failure" if failures_only else status
    reader = WorkshopLogReader()
    events = reader.query_events(grammar=grammar, stage=stage, status=selected_status, limit=limit)
    _emit_events(events, format=_resolve_format(format, json_output))


@app.command("stats")
def stats(
    format: OutputFormat = typer.Option("text", "--format", help="Output format."),
    json_output: bool = typer.Option(False, "--json", help="Shortcut for --format json."),
) -> None:
    """Show aggregate workshop log statistics."""
    reader = WorkshopLogReader()
    payload = reader.calculate_stats()
    output_format = _resolve_format(format, json_output)

    if output_format in {"json", "jsonl"}:
        typer.echo(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        return

    typer.echo(f"total_events: {payload['total_events']}")
    typer.echo(f"failures: {payload['failures']}")
    by_stage = payload.get("by_stage", {})
    avg_duration_ms = payload.get("avg_duration_ms", {})
    if by_stage:
        typer.echo("by_stage:")
        for stage in sorted(by_stage):
            avg = avg_duration_ms.get(stage)
            avg_segment = f" avg_ms={avg}" if avg is not None else ""
            typer.echo(f"  - {stage}: {by_stage[stage]}{avg_segment}")


@app.command("query")
def query(
    grammar: str | None = typer.Option(None, "--grammar", help="Filter by grammar."),
    stage: str | None = typer.Option(None, "--stage", help="Filter by stage."),
    status: str | None = typer.Option(None, "--status", help="Filter by status."),
    since: str | None = typer.Option(None, "--since", help="Inclusive lower timestamp bound (ISO-8601)."),
    until: str | None = typer.Option(None, "--until", help="Inclusive upper timestamp bound (ISO-8601)."),
    window: str | None = typer.Option(
        None,
        "--window",
        help="Relative time window ending now (e.g. 30m, 2h, 1d, 500ms).",
    ),
    limit: int | None = typer.Option(None, "--limit", min=1, help="Optional max number of events."),
    format: OutputFormat = typer.Option("text", "--format", help="Output format."),
    json_output: bool = typer.Option(False, "--json", help="Shortcut for --format json."),
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
    _emit_events(events, format=_resolve_format(format, json_output))
