"""Workshop CLI command group for Tree-sitter-to-CUE workflows."""

from __future__ import annotations

from pathlib import Path

import typer

from confidantic.workshop.services import (
    doctor_workshop_inputs,
    generate_workshop_schemas,
    validate_workshop_output,
)

app = typer.Typer(help="Workshop plumbing commands.", no_args_is_help=True)


@app.command("generate")
def generate(
    grammar: str = typer.Option(..., "--grammar", help="Grammar name."),
    node_types: Path = typer.Option(..., "--node-types", help="Path to node-types.json."),
    queries_dir: Path = typer.Option(..., "--queries-dir", help="Path to query .scm directory."),
    output_dir: Path = typer.Option(..., "--output-dir", help="Output directory for generated CUE files."),
) -> None:
    """Generate deterministic CUE artifacts from workshop Tree-sitter inputs."""
    result = generate_workshop_schemas(
        grammar=grammar,
        node_types_path=node_types,
        queries_dir=queries_dir,
        output_dir=output_dir,
    )
    for path in result.generated_files:
        typer.echo(path)
    raise typer.Exit(code=0)


@app.command("doctor")
def doctor(
    node_types: Path = typer.Option(..., "--node-types", help="Path to node-types.json."),
    queries_dir: Path = typer.Option(..., "--queries-dir", help="Path to query .scm directory."),
) -> None:
    """Check workshop input health and report diagnostics."""
    report = doctor_workshop_inputs(node_types_path=node_types, queries_dir=queries_dir)
    if report.ok:
        typer.echo("workshop doctor: OK")
        raise typer.Exit(code=0)

    for issue in report.issues:
        typer.echo(issue, err=True)
    raise typer.Exit(code=1)


@app.command("validate")
def validate(
    output_dir: Path = typer.Option(..., "--output-dir", help="Output directory containing generated CUE files."),
) -> None:
    """Validate generated workshop CUE outputs via CUE validation services."""
    result = validate_workshop_output(output_dir=output_dir)
    if result.ok:
        typer.echo("workshop validate: OK")
        raise typer.Exit(code=0)

    for error in result.errors:
        typer.echo(error, err=True)
    raise typer.Exit(code=1)
