"""Top-level Confidantic CLI plumbing."""

from __future__ import annotations

import typer

from .config import app as config_app
from .config import dump as config_dump
from .config import env as config_env
from .config import fingerprint as config_fingerprint
from .config import validate as config_validate
from .logs import app as logs_app
from .migrate import app as migrate_app
from .output import set_global_options
from .schema import app as schema_app
from .workshop import app as workshop_app

app = typer.Typer(help="Confidantic CLI.", no_args_is_help=True)
app.add_typer(config_app, name="config")
app.add_typer(schema_app, name="schema")
app.add_typer(workshop_app, name="workshop")
app.add_typer(logs_app, name="logs")
app.add_typer(migrate_app, name="migrate")


@app.callback()
def root_callback(
    ctx: typer.Context,
    verbose: int = typer.Option(0, "--verbose", "-v", count=True, help="Increase log verbosity."),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Emit minimal output."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON output."),
    no_color: bool = typer.Option(False, "--no-color", help="Disable ANSI color output."),
) -> None:
    """Store global output options for all command groups."""
    set_global_options(
        ctx,
        verbose=verbose,
        quiet=quiet,
        json_output=json_output,
        no_color=no_color,
    )


@app.command("validate")
def validate(ctx: typer.Context) -> None:
    """Legacy wrapper for `config validate`."""
    _ = ctx
    typer.echo("validate: not yet implemented")
    raise typer.Exit(code=0)


@app.command("dump")
def dump(
    ctx: typer.Context,
    format: str = typer.Option("json", "--format", help="Output format."),
) -> None:
    """Legacy wrapper for `config dump`."""
    config_dump(ctx, format=format)


@app.command("env")
def env(
    ctx: typer.Context,
    export: bool = typer.Option(False, "--export", help="Emit shell export syntax."),
) -> None:
    """Legacy wrapper for `config env`."""
    config_env(ctx, export=export)


@app.command("fingerprint")
def fingerprint(ctx: typer.Context) -> None:
    """Legacy wrapper for `config fingerprint`."""
    config_fingerprint(ctx)


def main() -> None:
    """CLI entrypoint exposed via pyproject scripts."""
    app()
