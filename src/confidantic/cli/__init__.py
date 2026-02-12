"""Top-level Confidantic CLI plumbing."""

from __future__ import annotations

import json
from os import environ

import typer

from confidantic.workshop.logging import WorkshopLogReader

from .workshop import app as workshop_app

app = typer.Typer(help="Confidantic CLI.", no_args_is_help=True)
app.add_typer(workshop_app, name="workshop")

logs_app = typer.Typer(help="Workshop provenance log commands.", no_args_is_help=True)
app.add_typer(logs_app, name="logs")


@app.command("validate")
def validate() -> None:
    """Validate active configuration state (plumbing command)."""
    typer.echo("validate: not yet implemented")
    raise typer.Exit(code=0)


@app.command("dump")
def dump(format: str = typer.Option("json", "--format", help="Output format.")) -> None:
    """Dump active configuration state (plumbing command)."""
    payload = {"format": format, "status": "ok"}
    if format == "json":
        typer.echo(json.dumps(payload, sort_keys=True))
    else:
        typer.echo(f"dump format={format}")
    raise typer.Exit(code=0)


@app.command("env")
def env(export: bool = typer.Option(False, "--export", help="Emit shell export syntax.")) -> None:
    """Show Confidantic environment values."""
    root = environ.get("CONFIDANTIC_ROOT", "")
    if export:
        typer.echo(f'export CONFIDANTIC_ROOT="{root}"')
    else:
        typer.echo(f"CONFIDANTIC_ROOT={root}")
    raise typer.Exit(code=0)


@app.command("fingerprint")
def fingerprint() -> None:
    """Show deterministic configuration fingerprint placeholder."""
    typer.echo("fingerprint: unavailable")
    raise typer.Exit(code=0)


@logs_app.command("show")
def logs_show(
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


@logs_app.command("stats")
def logs_stats() -> None:
    """Show aggregate workshop log statistics."""
    reader = WorkshopLogReader()
    typer.echo(json.dumps(reader.calculate_stats(), sort_keys=True))


def main() -> None:
    """CLI entrypoint exposed via pyproject scripts."""
    app()
