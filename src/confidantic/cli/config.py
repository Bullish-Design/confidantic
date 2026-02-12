"""Configuration CLI plumbing commands."""

from __future__ import annotations

from os import environ

import typer

from .output import emit

app = typer.Typer(help="Configuration plumbing commands.", no_args_is_help=True)


@app.command("validate")
def validate(ctx: typer.Context) -> None:
    """Validate active configuration state (plumbing command)."""
    emit(
        ctx,
        payload={"command": "config validate", "status": "ok", "message": "not yet implemented"},
        text="Configuration is valid (placeholder).",
        quiet_text="ok",
    )
    raise typer.Exit(code=0)


@app.command("dump")
def dump(
    ctx: typer.Context,
    format: str = typer.Option("json", "--format", help="Output format."),
) -> None:
    """Dump active configuration state (plumbing command)."""
    payload = {"command": "config dump", "format": format, "status": "ok"}
    emit(ctx, payload=payload, text=f"Config dump complete (format={format}).", quiet_text="ok")
    raise typer.Exit(code=0)


@app.command("env")
def env(
    ctx: typer.Context,
    export: bool = typer.Option(False, "--export", help="Emit shell export syntax."),
) -> None:
    """Show Confidantic environment values."""
    root = environ.get("CONFIDANTIC_ROOT", "")
    value = f'export CONFIDANTIC_ROOT="{root}"' if export else f"CONFIDANTIC_ROOT={root}"
    emit(
        ctx,
        payload={"command": "config env", "status": "ok", "export": export, "CONFIDANTIC_ROOT": root},
        text=value,
        quiet_text=value,
    )
    raise typer.Exit(code=0)


@app.command("fingerprint")
def fingerprint(ctx: typer.Context) -> None:
    """Show deterministic configuration fingerprint placeholder."""
    emit(
        ctx,
        payload={"command": "config fingerprint", "status": "ok", "fingerprint": "unavailable"},
        text="fingerprint: unavailable",
        quiet_text="unavailable",
    )
    raise typer.Exit(code=0)
