"""Workshop diagnostics and reporting helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from difflib import get_close_matches
from typing import Any, ClassVar, Literal

from confidantic.cue.wrapper import run_cue_vet
from confidantic.workshop.loaders import load_node_types, load_query_file


@dataclass(slots=True)
class DiagnosticIssue:
    """A single diagnostic finding."""

    model_fields: ClassVar[dict[str, Any]] = {
        "severity": str,
        "category": str,
        "message": str,
        "file_path": Path,
        "line_number": int,
        "suggestion": str,
    }

    severity: Literal["error", "warning", "info"]
    category: str
    message: str
    file_path: Path | None = None
    line_number: int | None = None
    suggestion: str | None = None

    def format(self) -> str:
        location = ""
        if self.file_path is not None:
            location = f" ({self.file_path}"
            if self.line_number is not None:
                location += f":{self.line_number}"
            location += ")"
        suggestion = f" Suggestion: {self.suggestion}" if self.suggestion else ""
        return f"[{self.severity}] {self.category}{location}: {self.message}{suggestion}"


@dataclass(slots=True)
class DiagnosticReport:
    """Grouped diagnostic report."""

    model_fields: ClassVar[dict[str, Any]] = {
        "grammar": str,
        "timestamp": datetime,
        "errors": list,
        "warnings": list,
        "info": list,
        "checks_run": int,
        "issues_found": int,
    }

    grammar: str
    timestamp: datetime
    errors: list[DiagnosticIssue] = field(default_factory=list)
    warnings: list[DiagnosticIssue] = field(default_factory=list)
    info: list[DiagnosticIssue] = field(default_factory=list)
    checks_run: int = 0
    issues_found: int = 0

    def is_healthy(self) -> bool:
        return len(self.errors) == 0

    def format_summary(self) -> str:
        status = "HEALTHY" if self.is_healthy() else "UNHEALTHY"
        return (
            f"Workshop diagnostics for {self.grammar}: {status}\n"
            f"Checks run: {self.checks_run} | "
            f"Errors: {len(self.errors)} | Warnings: {len(self.warnings)} | Info: {len(self.info)}"
        )


class WorkshopDoctor:
    """Diagnostic engine for workshop artifacts and generated CUE."""

    def __init__(
        self,
        grammar: str,
        node_types_path: Path,
        queries_dir: Path,
        schemas_dir: Path | None = None,
    ):
        self.grammar = grammar
        self.node_types_path = Path(node_types_path)
        self.queries_dir = Path(queries_dir)
        self.schemas_dir = Path(schemas_dir) if schemas_dir is not None else None
        self.issues: list[DiagnosticIssue] = []
        self._node_types: set[str] = set()
        self._query_references: list[tuple[str, Path, int | None]] = []

    def _add_issue(
        self,
        severity: Literal["error", "warning", "info"],
        category: str,
        message: str,
        *,
        file_path: Path | None = None,
        line_number: int | None = None,
        suggestion: str | None = None,
    ) -> None:
        self.issues.append(
            DiagnosticIssue(
                severity=severity,
                category=category,
                message=message,
                file_path=file_path,
                line_number=line_number,
                suggestion=suggestion,
            )
        )

    def _load_inputs(self) -> None:
        if not self.node_types_path.exists() or not self.queries_dir.exists():
            return
        node_types = load_node_types(self.node_types_path)
        self._node_types = {node.type for node in node_types.nodes}

        for query_path in sorted(self.queries_dir.glob("*.scm")):
            query = load_query_file(query_path, query_type=query_path.stem)
            for capture in query.captures:
                ref = capture.name.removeprefix("@").split(".", 1)[0].split(":", 1)[0]
                self._query_references.append((ref.replace("-", "_"), query_path, capture.line))

    def _check_missing_artifacts(self) -> None:
        if not self.node_types_path.exists():
            self._add_issue(
                "error", "missing_artifact", "Missing required node-types.json", file_path=self.node_types_path
            )
        elif not self.node_types_path.is_file():
            self._add_issue("error", "missing_artifact", "node-types path is not a file", file_path=self.node_types_path)

        if not self.queries_dir.exists():
            self._add_issue("error", "missing_artifact", "Missing required queries directory", file_path=self.queries_dir)
            return

        query_files = sorted(self.queries_dir.glob("*.scm"))
        if not query_files:
            self._add_issue("error", "missing_artifact", "No .scm query files found", file_path=self.queries_dir)

        required = self.queries_dir / "highlights.scm"
        if not required.exists():
            self._add_issue(
                "error",
                "missing_artifact",
                "Missing required query file highlights.scm",
                file_path=required,
            )

    def _check_unmapped_captures(self) -> None:
        if not self._node_types:
            return
        normalized_nodes = {node.replace("-", "_") for node in self._node_types}
        for name, file_path, line_number in self._query_references:
            if name in normalized_nodes:
                continue
            suggestion = None
            matches = get_close_matches(name, sorted(normalized_nodes), n=1, cutoff=0.75)
            if matches:
                suggestion = f"Did you mean @{matches[0]}?"
            self._add_issue(
                "warning",
                "unmapped_capture",
                f"Capture references unknown node type '{name}'",
                file_path=file_path,
                line_number=line_number,
                suggestion=suggestion,
            )

    def _check_orphaned_nodes(self) -> None:
        if not self._node_types:
            return
        referenced = {name for name, _, _ in self._query_references}
        orphaned = sorted(node for node in self._node_types if node.replace("-", "_") not in referenced)
        if orphaned:
            preview = ", ".join(orphaned[:8])
            self._add_issue(
                "info",
                "orphaned_nodes",
                f"{len(orphaned)} node types are not referenced in query captures: {preview}",
            )

    def _check_determinism(self) -> None:
        if self.schemas_dir is None or not self.schemas_dir.exists():
            return
        cue_files = sorted(self.schemas_dir.glob("*.cue"))
        if cue_files != sorted(cue_files, key=lambda path: path.name):
            self._add_issue("warning", "determinism", "CUE files are not in deterministic filename order")

        for cue_file in cue_files:
            lines = cue_file.read_text(encoding="utf-8").splitlines()
            defs = [line.strip() for line in lines if line.strip().startswith("#") and ":" in line]
            if defs and defs != sorted(defs):
                self._add_issue(
                    "warning", "determinism", "Definitions appear unsorted", file_path=cue_file
                )

            text = "\n".join(lines)
            if re.search(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", text):
                self._add_issue(
                    "warning", "determinism", "Timestamp-like value found in generated CUE", file_path=cue_file
                )
            if re.search(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b", text, re.I):
                self._add_issue(
                    "warning", "determinism", "UUID-like value found in generated CUE", file_path=cue_file
                )

    def _check_cue_validity(self) -> None:
        if self.schemas_dir is None or not self.schemas_dir.exists():
            return
        try:
            run_cue_vet(self.schemas_dir)
        except FileNotFoundError:
            self._add_issue("warning", "cue_validity", "cue binary unavailable; skipped cue vet")
        except Exception as exc:
            self._add_issue("error", "cue_validity", f"cue vet failed: {exc}", file_path=self.schemas_dir)

    def _check_performance(self) -> None:
        if len(self._node_types) > 1000:
            self._add_issue(
                "warning",
                "performance",
                f"Large node-types set ({len(self._node_types)}). Consider trimming grammar outputs.",
            )
        if len(self._query_references) > 500:
            self._add_issue(
                "warning",
                "performance",
                f"Large capture set ({len(self._query_references)}). Consider splitting query responsibilities.",
            )
        if self.schemas_dir and self.schemas_dir.exists():
            for cue_file in self.schemas_dir.glob("*.cue"):
                if cue_file.stat().st_size > 1_000_000:
                    self._add_issue(
                        "warning",
                        "performance",
                        "Generated CUE file exceeds 1MB",
                        file_path=cue_file,
                    )

    def run_diagnostics(self) -> DiagnosticReport:
        checks = [
            self._check_missing_artifacts,
            self._check_unmapped_captures,
            self._check_orphaned_nodes,
            self._check_determinism,
            self._check_cue_validity,
            self._check_performance,
        ]
        self._load_inputs()
        for check in checks:
            check()

        errors = [issue for issue in self.issues if issue.severity == "error"]
        warnings = [issue for issue in self.issues if issue.severity == "warning"]
        info = [issue for issue in self.issues if issue.severity == "info"]
        return DiagnosticReport(
            grammar=self.grammar,
            timestamp=datetime.now(timezone.utc),
            errors=errors,
            warnings=warnings,
            info=info,
            checks_run=len(checks),
            issues_found=len(self.issues),
        )


def format_diagnostic_report(report: DiagnosticReport, use_color: bool = True) -> str:
    """Format a diagnostic report for terminal display."""
    icons = {
        "error": "❌" if use_color else "ERROR",
        "warning": "⚠️" if use_color else "WARNING",
        "info": "ℹ️" if use_color else "INFO",
    }
    lines = [f"Workshop Diagnostics: {report.grammar}", report.format_summary(), ""]
    for label, issues in (("error", report.errors), ("warning", report.warnings), ("info", report.info)):
        if not issues:
            continue
        lines.append(f"{icons[label]} {label.title()}s")
        for issue in issues:
            lines.append(f"- {issue.format()}")
        lines.append("")
    return "\n".join(lines).strip()



def issue_payload(issue: DiagnosticIssue) -> dict[str, Any]:
    payload = {
        "severity": issue.severity,
        "category": issue.category,
        "message": issue.message,
        "file_path": str(issue.file_path) if issue.file_path is not None else None,
        "line_number": issue.line_number,
        "suggestion": issue.suggestion,
    }
    return {key: value for key, value in payload.items() if value is not None}

def export_diagnostic_report(
    report: DiagnosticReport,
    output_path: Path,
    format: Literal["json", "jsonl", "markdown"] = "json",
) -> None:
    """Export report in JSON/JSONL/Markdown formats."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "grammar": report.grammar,
        "timestamp": report.timestamp.isoformat().replace("+00:00", "Z"),
        "checks_run": report.checks_run,
        "issues_found": report.issues_found,
        "errors": [issue_payload(issue) for issue in report.errors],
        "warnings": [issue_payload(issue) for issue in report.warnings],
        "info": [issue_payload(issue) for issue in report.info],
    }

    if format == "json":
        destination.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return
    if format == "jsonl":
        destination.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        return

    lines = [f"# Workshop diagnostics: {report.grammar}", "", f"- Checks run: {report.checks_run}"]
    lines.append(f"- Errors: {len(report.errors)}")
    lines.append(f"- Warnings: {len(report.warnings)}")
    lines.append(f"- Info: {len(report.info)}")
    lines.append("")
    for heading, issues in (("Errors", report.errors), ("Warnings", report.warnings), ("Info", report.info)):
        lines.append(f"## {heading}")
        if not issues:
            lines.append("- None")
        for issue in issues:
            lines.append(f"- {issue.format()}")
        lines.append("")
    destination.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
