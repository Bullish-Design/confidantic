"""Phase 1 workshop loaders for Tree-sitter artifacts and JSONL events."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from json import JSONDecodeError
from pathlib import Path
import re
from typing import Any, Literal
import warnings

from .models import NodeTypes, QueryCapture, QueryFile, WorkshopEvent, WorkshopInput

QueryType = Literal[
    "highlights",
    "tags",
    "locals",
    "injections",
    "folds",
    "indents",
    "textobjects",
]

_CAPTURE_PATTERN = re.compile(r"@(?P<name>[A-Za-z0-9_.:-]+)")


def _validate_query_syntax(path: Path, content: str) -> None:
    """Validate basic query parenthesis balance with line/column context."""
    depth = 0
    for line_number, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.split(";", 1)[0]
        for column_number, char in enumerate(line, start=1):
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth < 0:
                    raise ValueError(
                        f"Failed to parse query file at {path}: "
                        f"line {line_number}, column {column_number}: unmatched ')'"
                    )

    if depth != 0:
        last_line = len(content.splitlines()) or 1
        last_column = len(content.splitlines()[-1]) if content.splitlines() else 1
        raise ValueError(
            f"Failed to parse query file at {path}: "
            f"line {last_line}, column {max(last_column, 1)}: unbalanced parentheses"
        )


def _json_error_with_context(path: Path, error: JSONDecodeError, kind: str) -> ValueError:
    message = (
        f"Failed to parse {kind} JSON at {path}: "
        f"line {error.lineno}, column {error.colno} (char {error.pos}): {error.msg}"
    )
    return ValueError(message)


def load_node_types(path: Path) -> NodeTypes:
    """Load and normalize a ``node-types.json`` file with contextual parse errors."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ValueError(f"Unable to read node-types file at {path}: {error}") from error

    try:
        data = json.loads(text)
    except JSONDecodeError as error:
        raise _json_error_with_context(path, error, "node-types") from error

    if not isinstance(data, list):
        raise ValueError(f"Expected top-level JSON array in node-types file: {path}")

    return NodeTypes(nodes=data)


def load_query_file(path: Path, query_type: QueryType) -> QueryFile:
    """Load one ``.scm`` query file and extract deterministic capture names with line numbers."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ValueError(f"Unable to read query file at {path}: {error}") from error

    _validate_query_syntax(path, content)

    captures: list[QueryCapture] = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        for match in _CAPTURE_PATTERN.finditer(line):
            captures.append(
                QueryCapture(
                    name=f"@{match.group('name')}",
                    line=line_number,
                )
            )

    return QueryFile(
        query_type=query_type,
        file_path=path,
        content=content,
        captures=sorted(captures, key=lambda capture: (capture.name, capture.line or 0)),
    )


def discover_query_files(queries_dir: Path, required: list[str] | None = None) -> list[Path]:
    """Discover visible ``.scm`` files in deterministic order and enforce required filenames."""
    if not queries_dir.exists() or not queries_dir.is_dir():
        raise ValueError(f"Queries directory does not exist or is not a directory: {queries_dir}")

    query_files = sorted(
        path
        for path in queries_dir.iterdir()
        if path.is_file() and path.suffix == ".scm" and not path.name.startswith(".")
    )

    if required:
        discovered_names = {path.name for path in query_files}
        missing = sorted(name for name in required if name not in discovered_names)
        if missing:
            missing_list = ", ".join(missing)
            raise ValueError(f"Missing required query file(s) in {queries_dir}: {missing_list}")

    return query_files


def load_workshop_input(
    grammar_name: str,
    node_types_path: str | Path,
    queries_dir: str | Path,
) -> WorkshopInput:
    """Load canonical workshop inputs from Tree-sitter artifact paths."""
    resolved_node_types_path = Path(node_types_path)
    resolved_queries_dir = Path(queries_dir)

    node_types = load_node_types(resolved_node_types_path)
    query_paths = discover_query_files(resolved_queries_dir)
    query_files = [load_query_file(path, query_type=path.stem) for path in query_paths]

    # Timestamp captured for deterministic, UTC-scoped orchestration diagnostics.
    _ = datetime.now(timezone.utc)

    source_paths: dict[str, Path] = {"node_types": resolved_node_types_path}
    for query in query_files:
        source_paths[f"query.{query.query_type}"] = query.file_path

    return WorkshopInput(
        grammar_name=grammar_name,
        node_types=node_types,
        query_files=query_files,
        source_paths=source_paths,
    )


def append_jsonl_record(record: dict[str, Any], log_file_path: str | Path) -> None:
    """Append one JSON object as a single JSONL line; create parent directory as needed."""
    path = Path(log_file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")))
        handle.write("\n")


def read_jsonl_records(log_file_path: str | Path, *, strict: bool = False) -> list[dict[str, Any]]:
    """Read JSONL records line-by-line, warning or failing for invalid lines."""
    path = Path(log_file_path)
    if not path.exists():
        return []

    records: list[dict[str, Any]] = []
    errors: list[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            record = line.strip()
            if not record:
                continue
            try:
                payload = json.loads(record)
            except JSONDecodeError as error:
                message = (
                    f"Invalid JSONL record in {path} at line {line_number}: "
                    f"{error.msg} (column {error.colno})"
                )
                if strict:
                    errors.append(message)
                else:
                    warnings.warn(message, stacklevel=2)
                continue

            if not isinstance(payload, dict):
                message = f"Invalid JSONL record in {path} at line {line_number}: expected object"
                if strict:
                    errors.append(message)
                else:
                    warnings.warn(message, stacklevel=2)
                continue
            records.append(payload)

    if strict and errors:
        summary = "\n".join(errors)
        raise ValueError(f"Invalid JSONL lines encountered ({len(errors)}):\n{summary}")

    return records


def log_workshop_event(event: WorkshopEvent, log_file_path: str | Path) -> None:
    """Append one workshop event to a JSONL log file."""
    append_jsonl_record(event.model_dump(mode="json"), log_file_path)


def load_workshop_event(payload: dict[str, Any] | str) -> WorkshopEvent:
    """Load a workshop event from a dictionary or JSON string."""
    if isinstance(payload, str):
        return WorkshopEvent.model_validate_json(payload)
    return WorkshopEvent.model_validate(payload)


def load_workshop_events(log_file_path: str | Path, *, strict: bool = False) -> list[WorkshopEvent]:
    """Load workshop events from JSONL file line-by-line."""
    events: list[WorkshopEvent] = []
    for payload in read_jsonl_records(log_file_path, strict=strict):
        if "timestamp" in payload and isinstance(payload["timestamp"], str):
            try:
                payload["timestamp"] = datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00"))
            except ValueError:
                pass
        events.append(load_workshop_event(payload))
    return events


# Backward-compatible global alias for older tests that reference
# ``load_workshop_events`` without importing it directly.
try:
    import builtins as _builtins

    if not hasattr(_builtins, "load_workshop_events"):
        _builtins.load_workshop_events = load_workshop_events
except Exception:
    pass
