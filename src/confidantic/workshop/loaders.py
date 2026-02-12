"""Phase 1 workshop loaders for Tree-sitter artifacts and JSONL events."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any

from .models import NodeTypes, QueryCapture, QueryFile, WorkshopEvent, WorkshopInput

_CAPTURE_PATTERN = re.compile(r"@[A-Za-z0-9_.:-]+")


def load_node_types(node_types_path: str | Path) -> NodeTypes:
    """Load and normalize a ``node-types.json`` file."""
    path = Path(node_types_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected list in node-types file: {path}")
    return NodeTypes(nodes=data)


def load_query_file(query_file_path: str | Path, query_type: str | None = None) -> QueryFile:
    """Load one ``.scm`` query file and extract deterministic capture names."""
    path = Path(query_file_path)
    content = path.read_text(encoding="utf-8")
    resolved_query_type = query_type or path.stem

    captures = sorted(set(_CAPTURE_PATTERN.findall(content)))
    capture_models = [QueryCapture(name=name) for name in captures]

    return QueryFile(
        query_type=resolved_query_type,
        file_path=path,
        content=content,
        captures=capture_models,
    )


def discover_query_files(queries_dir: str | Path) -> list[Path]:
    """Discover ``.scm`` files in deterministic order."""
    directory = Path(queries_dir)
    return sorted(p for p in directory.glob("*.scm") if p.is_file())


def load_workshop_input(
    grammar_name: str,
    node_types_path: str | Path,
    queries_dir: str | Path,
) -> WorkshopInput:
    """Load canonical workshop inputs from Tree-sitter artifact paths."""
    node_types = load_node_types(node_types_path)
    query_files = [load_query_file(path) for path in discover_query_files(queries_dir)]
    return WorkshopInput(
        grammar_name=grammar_name,
        node_types=node_types,
        query_files=query_files,
    )


def log_workshop_event(event: WorkshopEvent, log_file_path: str | Path) -> None:
    """Append one workshop event to a JSONL log file."""
    path = Path(log_file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(event.to_jsonl())
        handle.write("\n")


def load_workshop_event(payload: dict[str, Any] | str) -> WorkshopEvent:
    """Load a workshop event from a dictionary or JSON string."""
    if isinstance(payload, str):
        return WorkshopEvent.model_validate_json(payload)
    return WorkshopEvent.model_validate(payload)


def load_workshop_events(log_file_path: str | Path) -> list[WorkshopEvent]:
    """Load workshop events from JSONL file line-by-line."""
    path = Path(log_file_path)
    if not path.exists():
        return []

    events: list[WorkshopEvent] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            record = line.strip()
            if not record:
                continue
            payload = json.loads(record)
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
