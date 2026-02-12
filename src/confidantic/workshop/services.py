"""Workshop service helpers used by CLI plumbing commands."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from confidantic.cue.formatter import format_cue_directory, validate_cue_file
from confidantic.workshop.doctor import DiagnosticReport, WorkshopDoctor
from confidantic.workshop.generator import CueGenerator
from confidantic.workshop.loaders import load_workshop_input
from confidantic.workshop.logging import WorkshopLogger


@dataclass(frozen=True)
class WorkshopGenerateResult:
    """Result payload for workshop generation."""

    generated_files: tuple[Path, ...]


@dataclass(frozen=True)
class WorkshopDoctorResult:
    """Result payload for workshop diagnostics."""

    ok: bool
    issues: tuple[str, ...]
    report: DiagnosticReport


@dataclass(frozen=True)
class WorkshopValidateResult:
    """Result payload for workshop schema validation."""

    ok: bool
    errors: tuple[str, ...]


def generate_workshop_schemas(
    *,
    grammar: str,
    node_types_path: Path,
    queries_dir: Path,
    output_dir: Path,
    logger: WorkshopLogger | None = None,
) -> WorkshopGenerateResult:
    """Generate deterministic workshop CUE artifacts and format them."""
    run_logger = logger or WorkshopLogger()
    load_start = run_logger.log_stage_start("load", grammar)
    try:
        workshop_input = load_workshop_input(
            grammar_name=grammar,
            node_types_path=node_types_path,
            queries_dir=queries_dir,
        )
    except Exception as exc:
        run_logger.log_stage_end("load", grammar, load_start, success=False, error=str(exc))
        raise
    run_logger.log_stage_end("load", grammar, load_start, success=True)

    generate_start = run_logger.log_stage_start("generate", grammar)
    try:
        generator = CueGenerator(workshop_input)
        generated_files = tuple(generator.generate(output_dir=output_dir))
    except Exception as exc:
        run_logger.log_stage_end("generate", grammar, generate_start, success=False, error=str(exc))
        raise
    run_logger.log_stage_end("generate", grammar, generate_start, success=True, artifact_paths=list(generated_files))

    fmt_start = run_logger.log_stage_start("fmt", grammar)
    try:
        format_cue_directory(output_dir)
    except Exception as exc:
        run_logger.log_stage_end("fmt", grammar, fmt_start, success=False, error=str(exc))
        raise
    run_logger.log_stage_end("fmt", grammar, fmt_start, success=True, artifact_paths=[output_dir])
    return WorkshopGenerateResult(generated_files=generated_files)


def doctor_workshop_inputs(
    *,
    grammar: str,
    node_types_path: Path,
    queries_dir: Path,
    schemas_dir: Path | None = None,
    logger: WorkshopLogger | None = None,
) -> WorkshopDoctorResult:
    """Run deterministic workshop diagnostic checks."""
    run_logger = logger or WorkshopLogger()
    start = run_logger.log_stage_start("doctor", grammar)
    doctor = WorkshopDoctor(
        grammar=grammar,
        node_types_path=node_types_path,
        queries_dir=queries_dir,
        schemas_dir=schemas_dir,
    )
    report = doctor.run_diagnostics()
    issues = tuple(issue.format() for issue in report.errors + report.warnings + report.info)
    run_logger.log_stage_end(
        "doctor",
        grammar,
        start,
        success=report.is_healthy(),
        error=None if report.is_healthy() else "Doctor found issues",
        artifact_paths=[node_types_path, queries_dir] + ([schemas_dir] if schemas_dir else []),
    )
    return WorkshopDoctorResult(ok=report.is_healthy(), issues=issues, report=report)


def validate_workshop_output(
    *,
    output_dir: Path,
    grammar: str | None = None,
    logger: WorkshopLogger | None = None,
) -> WorkshopValidateResult:
    """Validate generated CUE files in deterministic sorted order."""
    run_logger = logger or WorkshopLogger()
    effective_grammar = grammar or output_dir.name
    start = run_logger.log_stage_start("vet", effective_grammar)

    cue_files = tuple(sorted(output_dir.glob("*.cue")))
    if not cue_files:
        error_message = f"No CUE files found in output directory: {output_dir}"
        run_logger.log_stage_end("vet", effective_grammar, start, success=False, error=error_message)
        return WorkshopValidateResult(ok=False, errors=(error_message,))

    errors: list[str] = []
    for cue_file in cue_files:
        success, error = validate_cue_file(cue_file)
        if not success:
            errors.append(error or f"Validation failed for {cue_file}")

    run_logger.log_stage_end(
        "vet",
        effective_grammar,
        start,
        success=not errors,
        error="; ".join(errors) if errors else None,
        artifact_paths=list(cue_files),
    )
    return WorkshopValidateResult(ok=not errors, errors=tuple(errors))
