"""Schema CLI command group for deterministic workshop export and validation."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from confidantic.workshop.services import generate_workshop_schemas, validate_workshop_output

from .output import fail

app = typer.Typer(help="Schema plumbing commands.", no_args_is_help=True)


def _emit_schema_vet_failure(*, output_dir: Path, grammar: str | None, message: str, errors: list[str]) -> None:
    """Emit schema vet failures as machine-parseable JSON on stderr."""
    typer.echo(
        json.dumps(
            {
                "command": "schema vet",
                "errors": errors,
                "grammar": grammar,
                "message": message,
                "ok": False,
                "output_dir": str(output_dir),
                "status": "error",
            },
            sort_keys=True,
        ),
        err=True,
    )
    raise typer.Exit(code=1)


def _emit_schema_success(payload: dict[str, object]) -> None:
    """Emit schema success payloads as deterministic JSON on stdout."""
    typer.echo(json.dumps(payload, sort_keys=True))


@app.command("export")
def export(
    ctx: typer.Context,
    grammar: str = typer.Option(..., "--grammar", help="Grammar name."),
    node_types: Path = typer.Option(..., "--node-types", help="Path to node-types.json."),
    queries_dir: Path = typer.Option(..., "--queries-dir", help="Path to query .scm directory."),
    output_dir: Path = typer.Option(..., "--output-dir", help="Output directory for generated CUE files."),
) -> None:
    """Export deterministic CUE schemas from Tree-sitter workshop inputs."""
    try:
        result = generate_workshop_schemas(
            grammar=grammar,
            node_types_path=node_types,
            queries_dir=queries_dir,
            output_dir=output_dir,
        )
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        fail(ctx, message=f"schema export failed: {exc}", payload={"command": "schema export", "status": "error"})
        raise typer.Exit(code=1)

    generated_files = list(getattr(result, "generated_files", []) or [])
    if not generated_files:
        fail(
            ctx,
            message="schema export failed: no files were generated",
            payload={"command": "schema export", "status": "error"},
        )
        raise typer.Exit(code=1)

    _emit_schema_success(
        {
            "command": "schema export",
            "generated_files": [str(path) for path in generated_files],
            "grammar": grammar,
            "output_dir": str(output_dir),
            "status": "ok",
        }
    )
    raise typer.Exit(code=0)


@app.command("vet")
def vet(
    ctx: typer.Context,
    output_dir: Path = typer.Option(..., "--output-dir", help="Output directory containing generated CUE files."),
    grammar: str | None = typer.Option(None, "--grammar", help="Grammar name for provenance logs."),
) -> None:
    """Validate generated CUE schema outputs via CUE vet services."""
    try:
        result = validate_workshop_output(output_dir=output_dir, grammar=grammar)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        _emit_schema_vet_failure(
            output_dir=output_dir,
            grammar=grammar,
            message=f"schema vet failed: {exc}",
            errors=[str(exc)],
        )

    if not result.ok:
        errors = [str(err) for err in (getattr(result, "errors", []) or [])]
        _emit_schema_vet_failure(
            output_dir=output_dir,
            grammar=grammar,
            message="schema vet failed",
            errors=errors,
        )

    _emit_schema_success(
        {
            "command": "schema vet",
            "grammar": grammar,
            "ok": True,
            "output_dir": str(output_dir),
            "status": "ok",
        }
    )
    raise typer.Exit(code=0)
