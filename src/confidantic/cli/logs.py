"""Workshop provenance log CLI commands."""

from __future__ import annotations

import json

import typer

from confidantic.workshop.logging import WorkshopLogReader

app = typer.Typer(help="Workshop provenance log commands.", no_args_is_help=True)


@app.command("show")
def show(
    limit: int = typer.Option(20, "--limit", help="Max events to show."),
    grammar: str | None = typer.Option(None, "--grammar", help="Filter by grammar."),
    stage: str | None = typer.Option(None, "--stage", help="Filter by stage."),
    failures_only: bool = typer.Option(False, "--failures-only", help="Show only failures."),
) -> None:
    """Show recent workshop log events."""
    reader = WorkshopLogReader()
    events = reader.get_recent(limit=limit)
    if grammar is not None:
        events = [event for event in events if event.grammar == grammar]
    if stage is not None:
        events = [event for event in events if event.stage == stage]
    if failures_only:
        events = [event for event in events if event.status == "failure"]

    for event in events:
        typer.echo(event.to_jsonl())


@app.command("stats")
def stats() -> None:
    """Show aggregate workshop log statistics."""
    reader = WorkshopLogReader()
    typer.echo(json.dumps(reader.calculate_stats(), sort_keys=True))


@app.command("query")
def query(
    grammar: str | None = typer.Option(None, "--grammar", help="Filter by grammar."),
    stage: str | None = typer.Option(None, "--stage", help="Filter by stage."),
    status: str | None = typer.Option(None, "--status", help="Filter by status."),
    limit: int | None = typer.Option(None, "--limit", min=1, help="Limit output records."),
) -> None:
    """Query workshop log events and emit deterministic JSON array output."""
    reader = WorkshopLogReader()
    events = sorted(reader.read_all(), key=lambda event: event.timestamp)

    if grammar is not None:
        events = [event for event in events if event.grammar == grammar]
    if stage is not None:
        events = [event for event in events if event.stage == stage]
    if status is not None:
        events = [event for event in events if event.status == status]
    if limit is not None:
        events = events[-limit:]

    payload = [event.model_dump(mode="json") for event in events]
    typer.echo(json.dumps(payload, sort_keys=True))
