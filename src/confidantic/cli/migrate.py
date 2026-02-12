"""Migration CLI commands for deprecated configuration patterns."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import typer

app = typer.Typer(help="Migration plumbing commands.", no_args_is_help=True)


class MigrateFormat(str, Enum):
    """Output format options for migrate commands."""
    JSON = "json"
    TEXT = "text"


@dataclass(frozen=True)
class DeprecatedPattern:
    pattern: re.Pattern[str]
    replacement: str
    message: str


@dataclass(frozen=True)
class Finding:
    line: int
    match: str
    replacement: str
    message: str


DEPRECATED_PATTERNS: tuple[DeprecatedPattern, ...] = (
    DeprecatedPattern(
        pattern=re.compile(r"^\s*config_root\s*="),
        replacement="root =",
        message="'config_root' is deprecated; use 'root'.",
    ),
    DeprecatedPattern(
        pattern=re.compile(r"^\s*profile\s*="),
        replacement="profile_default =",
        message="'profile' is deprecated; use 'profile_default'.",
    ),
    DeprecatedPattern(
        pattern=re.compile(r"^\s*data_file\s*="),
        replacement="data_files =",
        message="'data_file' is deprecated; use 'data_files'.",
    ),
)


def _scan_text(text: str) -> list[Finding]:
    findings: list[Finding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for deprecated in DEPRECATED_PATTERNS:
            if deprecated.pattern.search(line):
                findings.append(
                    Finding(
                        line=line_number,
                        match=line.strip(),
                        replacement=deprecated.replacement,
                        message=deprecated.message,
                    )
                )
    return findings


def _apply_migration(text: str) -> tuple[str, int]:
    updated_lines: list[str] = []
    replacements = 0

    for line in text.splitlines(keepends=True):
        updated = line
        for deprecated in DEPRECATED_PATTERNS:
            replaced, count = deprecated.pattern.subn(deprecated.replacement, updated, count=1)
            if count:
                replacements += count
                updated = replaced
        updated_lines.append(updated)

    return "".join(updated_lines), replacements


def _emit(payload: dict[str, object], *, format: MigrateFormat) -> None:
    if format == MigrateFormat.JSON:
        typer.echo(json.dumps(payload, sort_keys=True))
        return

    status = payload.get("status", "unknown")
    typer.echo(f"status={status}")
    if "message" in payload:
        typer.echo(str(payload["message"]))


@app.command("check")
def check(
    path: Path = typer.Option(Path("confidantic.toml"), "--path", help="Path to TOML config file."),
    format: MigrateFormat = typer.Option(MigrateFormat.JSON, "--format", help="Output format."),
) -> None:
    """Detect deprecated configuration patterns in a config file."""
    if not path.exists():
        _emit({"path": str(path), "status": "missing", "message": "config file not found"}, format=format)
        raise typer.Exit(code=1)

    text = path.read_text(encoding="utf-8")
    findings = _scan_text(text)
    payload = {
        "path": str(path),
        "status": "ok" if not findings else "deprecated-patterns-found",
        "findings": [finding.__dict__ for finding in findings],
    }
    _emit(payload, format=format)
    raise typer.Exit(code=0 if not findings else 2)


@app.command("apply")
def apply(
    path: Path = typer.Option(Path("confidantic.toml"), "--path", help="Path to TOML config file."),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create a .bak backup before writing."),
    format: MigrateFormat = typer.Option(MigrateFormat.JSON, "--format", help="Output format."),
) -> None:
    """Apply config migration for known deprecated patterns."""
    if not path.exists():
        _emit({"path": str(path), "status": "missing", "message": "config file not found"}, format=format)
        raise typer.Exit(code=1)

    original = path.read_text(encoding="utf-8")
    migrated, replacements = _apply_migration(original)

    if replacements == 0:
        _emit({"path": str(path), "status": "unchanged", "replacements": 0}, format=format)
        raise typer.Exit(code=0)

    backup_path: str | None = None
    if backup:
        backup_file = path.with_suffix(f"{path.suffix}.bak")
        backup_file.write_text(original, encoding="utf-8")
        backup_path = str(backup_file)

    path.write_text(migrated, encoding="utf-8")
    payload = {
        "path": str(path),
        "status": "migrated",
        "changed_files": [str(path)],
        "replacements": replacements,
        "backup": backup_path,
    }
    _emit(payload, format=format)
    raise typer.Exit(code=0)


@app.command("doctor")
def doctor(
    root: Path = typer.Option(Path("."), "--root", help="Project root to scan."),
    format: MigrateFormat = typer.Option(MigrateFormat.JSON, "--format", help="Output format."),
) -> None:
    """Run project-wide diagnostics for deprecated migration patterns."""
    if not root.exists():
        _emit({"root": str(root), "status": "missing", "message": "project root not found"}, format=format)
        raise typer.Exit(code=1)

    candidates: set[Path] = set()
    default_file = root / "confidantic.toml"
    if default_file.exists():
        candidates.add(default_file)

    for pattern in ("profiles/*.toml", ".devman/.config/**/*.toml"):
        candidates.update(root.glob(pattern))

    files = sorted(candidates)
    findings_by_file: dict[str, list[dict[str, object]]] = {}
    total_findings = 0

    for file_path in files:
        file_findings = _scan_text(file_path.read_text(encoding="utf-8"))
        if not file_findings:
            continue
        findings_by_file[str(file_path)] = [finding.__dict__ for finding in file_findings]
        total_findings += len(file_findings)

    payload = {
        "root": str(root),
        "scanned_files": [str(path) for path in files],
        "status": "ok" if total_findings == 0 else "deprecated-patterns-found",
        "files_with_findings": findings_by_file,
        "total_findings": total_findings,
    }
    _emit(payload, format=format)
    raise typer.Exit(code=0 if total_findings == 0 else 2)
