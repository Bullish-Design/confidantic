"""Workshop CLI command group for Tree-sitter-to-CUE workflows."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

import typer

from confidantic.workshop.doctor import export_diagnostic_report, format_diagnostic_report
from confidantic.workshop.services import doctor_workshop_inputs, generate_workshop_schemas, validate_workshop_output

from .output import emit, fail

app = typer.Typer(help="Workshop plumbing commands.", no_args_is_help=True)


class DiagnosticFormat(str, Enum):
    """Output format options for workshop doctor command."""
    TERMINAL = "terminal"
    JSON = "json"
    MARKDOWN = "markdown"
    JSONL = "jsonl"


@app.command("generate")
def generate(
    ctx: typer.Context,
    grammar: str = typer.Option(..., "--grammar", help="Grammar name."),
    node_types: Path = typer.Option(..., "--node-types", help="Path to node-types.json."),
    queries_dir: Path = typer.Option(..., "--queries-dir", help="Path to query .scm directory."),
    output_dir: Path = typer.Option(..., "--output-dir", help="Output directory for generated CUE files."),
) -> None:
    """Generate deterministic CUE artifacts from workshop Tree-sitter inputs."""
    try:
        result = generate_workshop_schemas(
            grammar=grammar,
            node_types_path=node_types,
            queries_dir=queries_dir,
            output_dir=output_dir,
        )
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        fail(ctx, message=f"workshop generate failed: {exc}", payload={"command": "workshop generate", "status": "error"})

    if not result.generated_files:
        fail(
            ctx,
            message="workshop generate failed: no files were generated",
            payload={"command": "workshop generate", "status": "error"},
        )

    emit(
        ctx,
        payload={
            "command": "workshop generate",
            "grammar": grammar,
            "output_dir": str(output_dir),
            "generated_files": [str(path) for path in result.generated_files],
            "status": "ok",
        },
        text=f"Generated {len(result.generated_files)} workshop schema file(s).",
        quiet_text="ok",
    )
    raise typer.Exit(code=0)


@app.command("doctor")
def doctor(
    ctx: typer.Context,
    grammar: str = typer.Option(..., "--grammar", help="Grammar name."),
    node_types: Path = typer.Option(..., "--node-types", help="Path to node-types.json."),
    queries_dir: Path = typer.Option(..., "--queries-dir", help="Path to query .scm directory."),
    schemas_dir: Path | None = typer.Option(None, "--schemas-dir", help="Optional generated CUE directory."),
    format: DiagnosticFormat = typer.Option(
        DiagnosticFormat.TERMINAL, "--format", help="Diagnostic output format."
    ),
    output: Path | None = typer.Option(None, "--output", help="Optional file to write report."),
) -> None:
    """Check workshop input health and report diagnostics."""
    try:
        result = doctor_workshop_inputs(
            grammar=grammar,
            node_types_path=node_types,
            queries_dir=queries_dir,
            schemas_dir=schemas_dir,
        )
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        fail(ctx, message=f"workshop doctor failed: {exc}", payload={"command": "workshop doctor", "status": "error"})

    report = result.report
    if format == DiagnosticFormat.TERMINAL:
        emit(
            ctx,
            payload={"command": "workshop doctor", "status": "ok", "healthy": report.is_healthy()},
            text=format_diagnostic_report(report),
            quiet_text="ok" if report.is_healthy() else "unhealthy",
        )
    elif output is None:
        fail(
            ctx,
            message="workshop doctor: --output is required for non-terminal formats",
            payload={"command": "workshop doctor", "status": "error"},
        )
    else:
        export_diagnostic_report(report, output_path=output, format=format)
        emit(
            ctx,
            payload={
                "command": "workshop doctor",
                "status": "ok",
                "healthy": report.is_healthy(),
                "output": str(output),
                "format": format,
            },
            text=f"Wrote diagnostic report: {output}",
            quiet_text=str(output),
        )

    raise typer.Exit(code=0 if report.is_healthy() else 1)


@app.command("validate")
def validate(
    ctx: typer.Context,
    output_dir: Path = typer.Option(..., "--output-dir", help="Output directory containing generated CUE files."),
    grammar: str | None = typer.Option(None, "--grammar", help="Grammar name for provenance logs."),
) -> None:
    """Validate generated workshop CUE outputs via CUE validation services."""
    try:
        result = validate_workshop_output(output_dir=output_dir, grammar=grammar)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        fail(ctx, message=f"workshop validate failed: {exc}", payload={"command": "workshop validate", "status": "error"})

    if not result.ok:
        fail(
            ctx,
            message="workshop validate failed",
            payload={
                "command": "workshop validate",
                "errors": list(result.errors),
                "grammar": grammar,
                "output_dir": str(output_dir),
                "status": "error",
            },
        )

    emit(
        ctx,
        payload={"command": "workshop validate", "grammar": grammar, "output_dir": str(output_dir), "status": "ok"},
        text="workshop validate: OK",
        quiet_text="ok",
    )
    raise typer.Exit(code=0)
