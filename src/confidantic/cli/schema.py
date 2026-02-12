"""Schema CLI plumbing commands."""

from __future__ import annotations

from pathlib import Path

import typer

from confidantic.workshop.services import generate_workshop_schemas, validate_workshop_output

app = typer.Typer(help="Schema plumbing commands.", no_args_is_help=True)


def _fail(message: str, *, code: int = 1) -> None:
    """Emit deterministic CLI error output and terminate."""
    typer.echo(message, err=True)
    raise typer.Exit(code=code)


@app.command("export")
def export(
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
        _fail(f"schema export failed: {exc}")

    if not result.generated_files:
        _fail("schema export failed: no files were generated")

    for path in result.generated_files:
        typer.echo(path)
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
