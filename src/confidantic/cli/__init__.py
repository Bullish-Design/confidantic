"""Top-level Confidantic CLI plumbing."""

from __future__ import annotations

import typer

from .config import app as config_app
from .config import dump as config_dump
from .config import env as config_env
from .config import fingerprint as config_fingerprint
from .config import validate as config_validate
from .logs import app as logs_app
from .workshop import app as workshop_app
from .schema import app as schema_app

app = typer.Typer(help="Confidantic CLI.", no_args_is_help=True)
app.add_typer(config_app, name="config")
app.add_typer(schema_app, name="schema")
app.add_typer(workshop_app, name="workshop")
app.add_typer(logs_app, name="logs")


@app.command("validate")
def validate() -> None:
    """Legacy wrapper for `config validate`."""
    config_validate()


@app.command("dump")
def dump(format: str = typer.Option("json", "--format", help="Output format.")) -> None:
    """Legacy wrapper for `config dump`."""
    config_dump(format=format)


@app.command("env")
def env(export: bool = typer.Option(False, "--export", help="Emit shell export syntax.")) -> None:
    """Legacy wrapper for `config env`."""
    config_env(export=export)


@app.command("fingerprint")
def fingerprint() -> None:
    """Legacy wrapper for `config fingerprint`."""
    config_fingerprint()


def main() -> None:
    """CLI entrypoint exposed via pyproject scripts."""
    app()
