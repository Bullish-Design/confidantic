"""Shared CLI output helpers with global option awareness."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

import click
from rich.console import Console
import typer


@dataclass(slots=True)
class GlobalOutputOptions:
    """Resolved root-level output options."""

    verbose: int = 0
    quiet: bool = False
    json_output: bool = False
    no_color: bool = False


def set_global_options(
    ctx: typer.Context,
    *,
    verbose: int,
    quiet: bool,
    json_output: bool,
    no_color: bool,
) -> None:
    """Store global output options in ``ctx.obj`` for all command groups."""
    ctx.obj = {
        "verbose": verbose,
        "quiet": quiet,
        "json": json_output,
        "no_color": no_color,
    }


def get_global_options(ctx: typer.Context | None = None) -> GlobalOutputOptions:
    """Load global options from the active Typer context."""
    context = ctx or click.get_current_context(silent=True)
    if context is None or not isinstance(context.obj, dict):
        return GlobalOutputOptions()

    return GlobalOutputOptions(
        verbose=int(context.obj.get("verbose", 0)),
        quiet=bool(context.obj.get("quiet", False)),
        json_output=bool(context.obj.get("json", False)),
        no_color=bool(context.obj.get("no_color", False)),
    )


def emit(
    ctx: typer.Context | None = None,
    *,
    payload: dict[str, Any] | list[Any] | None = None,
    text: str | None = None,
    quiet_text: str | None = None,
    err: bool = False,
) -> None:
    """Emit command output based on global options.

    Priority: JSON output -> quiet text -> rich text.
    """
    options = get_global_options(ctx)

    if options.json_output:
        data: Any = payload if payload is not None else {"message": text or ""}
        typer.echo(json.dumps(data, sort_keys=True), err=err)
        return

    if options.quiet:
        if quiet_text is not None:
            typer.echo(quiet_text, err=err)
        elif text is not None:
            typer.echo(text, err=err)
        return

    message = text if text is not None else json.dumps(payload or {}, sort_keys=True, indent=2)
    Console(stderr=err, no_color=options.no_color).print(message)


def fail(
    ctx: typer.Context | None = None,
    *,
    message: str,
    payload: dict[str, Any] | None = None,
    code: int = 1,
) -> None:
    """Emit failure output with global formatting rules and exit."""
    emit(ctx, payload=payload, text=message, quiet_text=message, err=True)
    raise typer.Exit(code=code)
