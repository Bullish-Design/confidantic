"""Workflow-oriented CLI commands replacing Just recipe orchestration."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

import typer

from confidantic.cue.wrapper import run_cue_fmt, run_cue_vet
from confidantic.workshop.services import (
    doctor_workshop_inputs,
    generate_workshop_schemas,
    validate_workshop_output,
)

from .output import emit, fail

app = typer.Typer(help="Workflow commands for Tree-sitter-to-CUE automation.", no_args_is_help=True)


@dataclass(frozen=True)
class WorkflowPaths:
    grammar: str
    root: Path

    @property
    def node_types(self) -> Path:
        return self.root / "build" / "treesitter" / self.grammar / "node-types.json"

    @property
    def queries_dir(self) -> Path:
        return self.root / "build" / "treesitter" / self.grammar / "queries"

    @property
    def output_dir(self) -> Path:
        return self.root / "build" / "schemas" / "cue" / self.grammar


def _resolve_paths(grammar: str, cwd: Path | None = None) -> WorkflowPaths:
    return WorkflowPaths(grammar=grammar, root=(cwd or Path.cwd()).resolve())


def _ensure_inputs(paths: WorkflowPaths) -> None:
    if not paths.node_types.exists():
        raise FileNotFoundError(f"missing required Tree-sitter artifact: {paths.node_types}")
    if not paths.queries_dir.exists():
        raise FileNotFoundError(f"missing required query directory: {paths.queries_dir}")
    if not any(paths.queries_dir.glob("*.scm")):
        raise FileNotFoundError(f"no .scm query files found in: {paths.queries_dir}")


def _ensure_output_dir(paths: WorkflowPaths) -> None:
    if not paths.output_dir.exists():
        raise FileNotFoundError(f"missing generated schema directory: {paths.output_dir}")
    if not any(paths.output_dir.glob("*.cue")):
        raise FileNotFoundError(f"no generated CUE files found in: {paths.output_dir}")


@app.command("doctor")
def doctor(
    ctx: typer.Context,
    grammar: str = typer.Argument(..., help="Grammar name."),
) -> None:
    """Validate workshop inputs and report diagnostics."""
    paths = _resolve_paths(grammar)
    try:
        _ensure_inputs(paths)
        result = doctor_workshop_inputs(
            grammar=grammar,
            node_types_path=paths.node_types,
            queries_dir=paths.queries_dir,
            schemas_dir=paths.output_dir if paths.output_dir.exists() else None,
        )
    except Exception as exc:  # pragma: no cover
        fail(ctx, message=f"workflow doctor failed: {exc}", payload={"command": "workflow doctor", "status": "error"})

    emit(
        ctx,
        payload={"command": "workflow doctor", "status": "ok", "grammar": grammar, "healthy": result.ok},
        text="workflow doctor: OK" if result.ok else "workflow doctor: unhealthy",
        quiet_text="ok" if result.ok else "unhealthy",
    )
    raise typer.Exit(code=0 if result.ok else 1)


@app.command("generate")
def generate(
    ctx: typer.Context,
    grammar: str = typer.Argument(..., help="Grammar name."),
) -> None:
    """Generate and format deterministic CUE schemas from build conventions."""
    paths = _resolve_paths(grammar)
    try:
        _ensure_inputs(paths)
        paths.output_dir.mkdir(parents=True, exist_ok=True)
        result = generate_workshop_schemas(
            grammar=grammar,
            node_types_path=paths.node_types,
            queries_dir=paths.queries_dir,
            output_dir=paths.output_dir,
        )
    except Exception as exc:  # pragma: no cover
        fail(ctx, message=f"workflow generate failed: {exc}", payload={"command": "workflow generate", "status": "error"})

    emit(
        ctx,
        payload={
            "command": "workflow generate",
            "status": "ok",
            "grammar": grammar,
            "generated_files": [str(path) for path in result.generated_files],
            "output_dir": str(paths.output_dir),
        },
        text=f"Generated {len(result.generated_files)} files.",
        quiet_text="ok",
    )
    raise typer.Exit(code=0)


@app.command("fmt")
def fmt(
    ctx: typer.Context,
    grammar: str = typer.Argument(..., help="Grammar name."),
) -> None:
    """Format generated CUE schemas for a grammar."""
    paths = _resolve_paths(grammar)
    try:
        _ensure_output_dir(paths)
        run_cue_fmt(paths.output_dir)
    except Exception as exc:  # pragma: no cover
        fail(ctx, message=f"workflow fmt failed: {exc}", payload={"command": "workflow fmt", "status": "error"})

    emit(
        ctx,
        payload={"command": "workflow fmt", "status": "ok", "grammar": grammar, "output_dir": str(paths.output_dir)},
        text="workflow fmt: OK",
        quiet_text="ok",
    )
    raise typer.Exit(code=0)


@app.command("vet")
def vet(
    ctx: typer.Context,
    grammar: str = typer.Argument(..., help="Grammar name."),
) -> None:
    """Run CUE validation for generated schemas."""
    paths = _resolve_paths(grammar)
    try:
        _ensure_output_dir(paths)
        result = validate_workshop_output(output_dir=paths.output_dir, grammar=grammar)
    except Exception as exc:  # pragma: no cover
        fail(ctx, message=f"workflow vet failed: {exc}", payload={"command": "workflow vet", "status": "error"})

    if not result.ok:
        fail(
            ctx,
            message="workflow vet failed",
            payload={"command": "workflow vet", "status": "error", "grammar": grammar, "errors": list(result.errors)},
        )

    emit(
        ctx,
        payload={"command": "workflow vet", "status": "ok", "grammar": grammar, "output_dir": str(paths.output_dir)},
        text="workflow vet: OK",
        quiet_text="ok",
    )
    raise typer.Exit(code=0)


@app.command("workshop")
def workshop(
    ctx: typer.Context,
    grammar: str = typer.Argument(..., help="Grammar name."),
) -> None:
    """Run doctor + generate + vet workflow in one command."""
    paths = _resolve_paths(grammar)
    try:
        _ensure_inputs(paths)
        doctor_result = doctor_workshop_inputs(
            grammar=grammar,
            node_types_path=paths.node_types,
            queries_dir=paths.queries_dir,
            schemas_dir=paths.output_dir if paths.output_dir.exists() else None,
        )
        if not doctor_result.ok:
            raise RuntimeError("doctor reported unhealthy inputs")
        paths.output_dir.mkdir(parents=True, exist_ok=True)
        generate_workshop_schemas(
            grammar=grammar,
            node_types_path=paths.node_types,
            queries_dir=paths.queries_dir,
            output_dir=paths.output_dir,
        )
        vet_result = validate_workshop_output(output_dir=paths.output_dir, grammar=grammar)
        if not vet_result.ok:
            raise RuntimeError("; ".join(vet_result.errors))
    except Exception as exc:  # pragma: no cover
        fail(ctx, message=f"workflow workshop failed: {exc}", payload={"command": "workflow workshop", "status": "error"})

    emit(
        ctx,
        payload={"command": "workflow workshop", "status": "ok", "grammar": grammar, "output_dir": str(paths.output_dir)},
        text="workflow workshop: OK",
        quiet_text="ok",
    )
    raise typer.Exit(code=0)


@app.command("data-vet")
def data_vet(
    ctx: typer.Context,
    grammar: str = typer.Argument(..., help="Grammar name."),
    data_path: Path | None = typer.Option(None, "--data-path", help="Dataset path to validate."),
) -> None:
    """Validate dataset against grammar schema directory via cue vet."""
    paths = _resolve_paths(grammar)
    default_data = Path(os.environ.get("CONFIDANTIC_DATA_PATH", "")) if os.environ.get("CONFIDANTIC_DATA_PATH") else None
    if default_data is None:
        root = Path(os.environ.get("CONFIDANTIC_ROOT", Path.cwd() / ".devman" / ".config"))
        default_data = root / "data"
    selected_data = data_path or default_data

    try:
        _ensure_output_dir(paths)
        if not selected_data.exists():
            raise FileNotFoundError(f"missing dataset path for validation: {selected_data}")
        run_cue_vet(selected_data, schema=paths.output_dir)
    except Exception as exc:  # pragma: no cover
        fail(ctx, message=f"workflow data-vet failed: {exc}", payload={"command": "workflow data-vet", "status": "error"})

    emit(
        ctx,
        payload={
            "command": "workflow data-vet",
            "status": "ok",
            "grammar": grammar,
            "data_path": str(selected_data),
            "schema_dir": str(paths.output_dir),
        },
        text="workflow data-vet: OK",
        quiet_text="ok",
    )
    raise typer.Exit(code=0)
