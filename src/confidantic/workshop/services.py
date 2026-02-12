"""Workshop service helpers used by CLI plumbing commands."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from confidantic.cue.formatter import format_cue_directory, validate_cue_file
from confidantic.workshop.generator import CueGenerator
from confidantic.workshop.loaders import load_workshop_input


@dataclass(frozen=True)
class WorkshopGenerateResult:
    """Result payload for workshop generation."""

    generated_files: tuple[Path, ...]


@dataclass(frozen=True)
class WorkshopDoctorResult:
    """Result payload for workshop diagnostics."""

    ok: bool
    issues: tuple[str, ...]


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
) -> WorkshopGenerateResult:
    """Generate deterministic workshop CUE artifacts and format them."""
    workshop_input = load_workshop_input(
        grammar_name=grammar,
        node_types_path=node_types_path,
        queries_dir=queries_dir,
    )
    generator = CueGenerator(workshop_input)
    generated_files = tuple(generator.generate(output_dir=output_dir))
    format_cue_directory(output_dir)
    return WorkshopGenerateResult(generated_files=generated_files)


def doctor_workshop_inputs(*, node_types_path: Path, queries_dir: Path) -> WorkshopDoctorResult:
    """Run lightweight deterministic checks against required workshop inputs."""
    issues: list[str] = []

    if not node_types_path.exists():
        issues.append(f"Missing required node types file: {node_types_path}")
    if not queries_dir.exists():
        issues.append(f"Missing required queries directory: {queries_dir}")
    if queries_dir.exists() and not queries_dir.is_dir():
        issues.append(f"Queries path is not a directory: {queries_dir}")

    if not issues and not list(sorted(queries_dir.glob("*.scm"))):
        issues.append(f"No query files found in: {queries_dir}")

    return WorkshopDoctorResult(ok=not issues, issues=tuple(issues))


def validate_workshop_output(*, output_dir: Path) -> WorkshopValidateResult:
    """Validate generated CUE files in deterministic sorted order."""
    cue_files = tuple(sorted(output_dir.glob("*.cue")))
    if not cue_files:
        return WorkshopValidateResult(
            ok=False,
            errors=(f"No CUE files found in output directory: {output_dir}",),
        )

    errors: list[str] = []
    for cue_file in cue_files:
        success, error = validate_cue_file(cue_file)
        if not success:
            errors.append(error or f"Validation failed for {cue_file}")

    return WorkshopValidateResult(ok=not errors, errors=tuple(errors))
