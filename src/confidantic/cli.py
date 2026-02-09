"""Confidantic CLI — plumbing-only commands.

Commands:
- validate: Validate configuration and report errors.
- dump:     Output resolved configuration as JSON.
- env:      Emit KEY=VALUE lines for shell consumption.
- fingerprint: Print the configuration fingerprint.

The CLI calls resolver/services — it does not contain business logic.
Output is machine-friendly and redacted by default.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer

from confidantic.core.errors import ConfidanticError
from confidantic.core.resolver import resolve
from confidantic.core.snapshot import build_snapshot, snapshot_fingerprint

app = typer.Typer(
    name="confidantic",
    help="Deterministic configuration management for devman-managed projects.",
    no_args_is_help=True,
)


def _resolve_or_exit(
    profile: str | None = None,
    config_root: Path | None = None,
):
    """Run the resolver, printing errors and exiting on failure."""
    try:
        return resolve(profile=profile, config_root=config_root)
    except ConfidanticError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc


@app.command()
def validate(
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile name."),
    config_root: Optional[Path] = typer.Option(
        None, "--root", "-r", help="CONFIDANTIC_ROOT override."
    ),
) -> None:
    """Validate configuration: load, merge, and check for errors."""
    _resolve_or_exit(profile=profile, config_root=config_root)
    typer.echo("ok")


@app.command()
def dump(
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile name."),
    config_root: Optional[Path] = typer.Option(
        None, "--root", "-r", help="CONFIDANTIC_ROOT override."
    ),
    format: str = typer.Option("json", "--format", "-f", help="Output format (json)."),
    no_redact: bool = typer.Option(
        False, "--no-redact", help="Disable redaction (unsafe)."
    ),
) -> None:
    """Output the resolved configuration snapshot."""
    bundle = _resolve_or_exit(profile=profile, config_root=config_root)

    if format != "json":
        typer.echo(f"error: unsupported format '{format}'", err=True)
        raise typer.Exit(code=1)

    snapshot = build_snapshot(bundle, redact=not no_redact)
    typer.echo(snapshot)


@app.command()
def env(
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile name."),
    config_root: Optional[Path] = typer.Option(
        None, "--root", "-r", help="CONFIDANTIC_ROOT override."
    ),
) -> None:
    """Emit resolved configuration as KEY=VALUE lines.

    Flattens the config tree using underscore-separated uppercase keys.
    """
    bundle = _resolve_or_exit(profile=profile, config_root=config_root)
    lines = _flatten_to_env(bundle.to_redacted_dict().get("config", {}))
    for line in sorted(lines):
        typer.echo(line)


@app.command()
def fingerprint(
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile name."),
    config_root: Optional[Path] = typer.Option(
        None, "--root", "-r", help="CONFIDANTIC_ROOT override."
    ),
) -> None:
    """Print the SHA-256 fingerprint of the resolved configuration."""
    bundle = _resolve_or_exit(profile=profile, config_root=config_root)
    fp = snapshot_fingerprint(bundle)
    typer.echo(fp)


def _flatten_to_env(
    data: dict, prefix: str = "", sep: str = "_"
) -> list[str]:
    """Flatten a nested dict to KEY=VALUE lines."""
    lines: list[str] = []
    for key in sorted(data.keys()):
        value = data[key]
        env_key = f"{prefix}{sep}{key}".upper().lstrip(sep) if prefix else key.upper()
        if isinstance(value, dict):
            lines.extend(_flatten_to_env(value, prefix=env_key, sep=sep))
        elif isinstance(value, list):
            # Serialize lists as JSON strings
            import json
            lines.append(f"{env_key}={json.dumps(value)}")
        else:
            lines.append(f"{env_key}={value}")
    return lines


def main() -> None:
    """Entry point for the confidantic CLI."""
    app()
