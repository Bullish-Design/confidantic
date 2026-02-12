"""Schema CLI command group for deterministic workshop export and validation."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from confidantic.workshop.services import generate_workshop_schemas, validate_workshop_output

app = typer.Typer(help="Schema plumbing commands.", no_args_is_help=True)


# def _fail(message: str, *, code: int = 1) -> None:
#     """Emit deterministic CLI error output and terminate."""
#     typer.echo(message, err=True)
    
def _emit_json(payload: dict[str, object], *, err: bool = False) -> None:
    """Emit compact deterministic JSON output for CI log parsing."""
    typer.echo(json.dumps(payload, sort_keys=True), err=err)


def _fail(command: str, message: str, *, code: int = 1) -> None:
    """Emit machine-parseable CLI error output and terminate."""
    _emit_json({"command": command, "message": message, "status": "error"}, err=True)
    raise typer.Exit(code=code)


@app.command("export")
def export(
    grammar: str = typer.Option(..., "--grammar", help="Grammar name."),
    node_types: Path = typer.Option(..., "--node-types", help="Path to node-types.json."),
    queries_dir: Path = typer.Option(..., "--queries-dir", help="Path to query .scm directory."),
    output_dir: Path = typer.Option(..., "--output-dir", help="Output directory for generated CUE files."),
) -> None:
    """Export deterministic CUE schemas from Tree-sitter workshop inputs."""
    """Generate and format deterministic CUE schema files from Tree-sitter inputs."""
    try:
        result = generate_workshop_schemas(
            grammar=grammar,
            node_types_path=node_types,
            queries_dir=queries_dir,
            output_dir=output_dir,
        )
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        _fail(f"schema export failed: {exc}")

    if not result.generated_files:
        _fail("schema export failed: no files were generated")

    for path in result.generated_files:
        typer.echo(path)
        _fail("schema export", str(exc))

    if not result.generated_files:
        _fail("schema export", "no files were generated")

    _emit_json(
        {
            "command": "schema export",
            "generated_files": [str(path) for path in result.generated_files],
            "grammar": grammar,
            "output_dir": str(output_dir),
            "status": "ok",
        }
    )
    raise typer.Exit(code=0)


@app.command("vet")
def vet(
    output_dir: Path = typer.Option(..., "--output-dir", help="Output directory containing generated CUE files."),
    grammar: str | None = typer.Option(None, "--grammar", help="Grammar name for provenance logs."),
) -> None:
    """Validate generated CUE schema outputs via CUE vet services."""
    try:
        result = validate_workshop_output(output_dir=output_dir, grammar=grammar)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        _fail(f"schema vet failed: {exc}")

    if result.ok:
        typer.echo("schema vet: OK")
        raise typer.Exit(code=0)

    for error in result.errors:
        typer.echo(error, err=True)
    raise typer.Exit(code=1)
    grammar: str = typer.Option(..., "--grammar", help="Grammar name."),
    output_dir: Path = typer.Option(..., "--output-dir", help="Directory containing generated CUE files."),
) -> None:
    """Validate generated schema files via deterministic CUE vet workflow."""
    try:
        result = validate_workshop_output(output_dir=output_dir, grammar=grammar)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        _fail("schema vet", str(exc))

    if not result.ok:
        _emit_json(
            {
                "command": "schema vet",
                "errors": list(result.errors),
                "grammar": grammar,
                "output_dir": str(output_dir),
                "status": "error",
            },
            err=True,
        )
        raise typer.Exit(code=1)

    _emit_json(
        {
            "command": "schema vet",
            "grammar": grammar,
            "output_dir": str(output_dir),
            "status": "ok",
        }
    )
    raise typer.Exit(code=0)
