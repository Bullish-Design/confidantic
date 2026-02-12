"""Top-level Confidantic CLI plumbing."""

from __future__ import annotations

import json
from os import environ

import typer

from .workshop import app as workshop_app

app = typer.Typer(help="Confidantic CLI.", no_args_is_help=True)
app.add_typer(workshop_app, name="workshop")


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


def main() -> None:
    """CLI entrypoint exposed via pyproject scripts."""
    app()
