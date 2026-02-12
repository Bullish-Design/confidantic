"""Phase 1 workshop models for Tree-sitter artifact ingestion."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, ClassVar

_REDACTED = "[REDACTED]"
_SENSITIVE_KEYS = ("secret", "token", "password", "api_key", "private_key", "credential")


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    return value


def to_redacted_dict(value: Any) -> Any:
    """Return a recursively redacted representation safe for logs and snapshots."""
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    elif hasattr(value, "__dataclass_fields__"):
        value = asdict(value)

    if isinstance(value, dict):
        output: dict[str, Any] = {}
        for key, item in value.items():
            key_str = str(key)
            if any(flag in key_str.lower() for flag in _SENSITIVE_KEYS):
                output[key_str] = _REDACTED
            else:
                output[key_str] = to_redacted_dict(item)
        return output

    if isinstance(value, list):
        return [to_redacted_dict(item) for item in value]

    if isinstance(value, str):
        if "/" in value or "\\" in value:
            return _REDACTED
        return value

    return _to_jsonable(value)


@dataclass(slots=True)
class NodeType:
    """A single node-type entry from Tree-sitter's ``node-types.json``."""

    model_fields: ClassVar[dict[str, Any]] = {"type": str, "named": bool}

    type: str
    named: bool
    fields: dict[str, object] = field(default_factory=dict)
    children: dict[str, object] | None = None
    subtypes: list[dict[str, object]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.type, str) or not self.type:
            raise ValueError("NodeType.type must be a non-empty string")
        if not isinstance(self.named, bool):
            raise ValueError("NodeType.named must be a boolean")


@dataclass(slots=True)
class NodeTypes:
    """Deterministic collection of node types."""

    model_fields: ClassVar[dict[str, Any]] = {"nodes": list}

    nodes: list[NodeType | dict[str, Any]]

    def __post_init__(self) -> None:
        coerced: list[NodeType] = []
        for node in self.nodes:
            if isinstance(node, NodeType):
                coerced.append(node)
            else:
                coerced.append(NodeType(**node))
        # Empty arrays are valid Tree-sitter artifacts and should remain stable.
        self.nodes = sorted(coerced, key=lambda n: n.type)

    def model_dump(self, mode: str = "python") -> dict[str, Any]:
        return {"nodes": [_to_jsonable(asdict(node)) for node in self.nodes]}


@dataclass(slots=True, frozen=True)
class QueryCapture:
    """A capture token parsed from a Tree-sitter query file."""

    model_fields: ClassVar[dict[str, Any]] = {"name": str}

    name: str
    line: int | None = None
    pattern: str | None = None
    line_number: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("QueryCapture.name must be a non-empty string")
        if not self.name.startswith("@"):
            raise ValueError("QueryCapture.name must start with '@'")
        if self.pattern is not None and not isinstance(self.pattern, str):
            raise ValueError("QueryCapture.pattern must be a string when provided")
        if not isinstance(self.line_number, int) or self.line_number < 0:
            raise ValueError("QueryCapture.line_number must be a non-negative integer")


@dataclass(slots=True)
class QueryFile:
    """A deterministic representation of one ``.scm`` query file."""

    model_fields: ClassVar[dict[str, Any]] = {"query_type": str, "file_path": Path}

    query_type: str
    file_path: Path
    content: str
    captures: list[QueryCapture | dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.query_type, str) or not self.query_type:
            raise ValueError("QueryFile.query_type must be a non-empty string")
        self.file_path = Path(self.file_path)
        if not str(self.file_path):
            raise ValueError("QueryFile.file_path must be a valid path")
        if not isinstance(self.content, str):
            raise ValueError("QueryFile.content must be a string")

        normalized: list[QueryCapture] = []
        for capture in self.captures:
            if isinstance(capture, QueryCapture):
                normalized.append(capture)
            else:
                normalized.append(QueryCapture(**capture))
        self.captures = sorted(normalized, key=lambda c: (c.name, c.line if c.line is not None else -1))


@dataclass(slots=True)
class WorkshopInput:
    """Workshop source inputs for deterministic generation."""

    model_fields: ClassVar[dict[str, Any]] = {
        "grammar_name": str,
        "node_types": NodeTypes,
        "query_files": list,
        "timestamp": datetime,
        "source_paths": dict,
    }

    grammar_name: str
    node_types: NodeTypes | dict[str, Any]
    query_files: list[QueryFile | dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime(1970, 1, 1, tzinfo=timezone.utc))
    source_paths: dict[str, Path | str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.grammar_name, str) or not self.grammar_name.strip():
            raise ValueError("WorkshopInput.grammar_name must be a non-empty string")

        if not isinstance(self.node_types, NodeTypes):
            self.node_types = NodeTypes(**self.node_types)

        normalized: list[QueryFile] = []
        for query_file in self.query_files:
            if isinstance(query_file, QueryFile):
                normalized.append(query_file)
            else:
                normalized.append(QueryFile(**query_file))
        self.query_files = sorted(normalized, key=lambda q: (q.query_type, str(q.file_path)))

        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))
        if not isinstance(self.timestamp, datetime) or self.timestamp.tzinfo is None:
            raise ValueError("WorkshopInput.timestamp must be timezone-aware (UTC)")
        self.timestamp = self.timestamp.astimezone(timezone.utc)

        normalized_sources: dict[str, Path] = {}
        for key, path in sorted(self.source_paths.items(), key=lambda item: item[0]):
            if not isinstance(key, str) or not key:
                raise ValueError("WorkshopInput.source_paths keys must be non-empty strings")
            as_path = Path(path)
            if not str(as_path):
                raise ValueError(f"WorkshopInput.source_paths[{key!r}] must be a valid path")
            normalized_sources[key] = as_path
        self.source_paths = normalized_sources

    def model_dump(self, mode: str = "python") -> dict[str, Any]:
        payload = {
            "grammar_name": self.grammar_name,
            "node_types": self.node_types.model_dump(mode=mode),
            "query_files": [_to_jsonable(asdict(query_file)) for query_file in self.query_files],
            "timestamp": self.timestamp,
            "source_paths": {key: str(path) for key, path in self.source_paths.items()},
        }
        return _to_jsonable(payload) if mode == "json" else payload

    def fingerprint(self) -> str:
        """Return a deterministic fingerprint of normalized workshop input."""
        normalized = self.model_dump(mode="json")
        payload = json.dumps(normalized, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(slots=True)
class WorkshopEvent:
    """JSONL event emitted during workshop processing."""

    model_fields: ClassVar[dict[str, Any]] = {
        "timestamp": datetime,
        "stage": str,
        "status": str,
        "grammar": str,
    }

    timestamp: datetime
    stage: str
    status: str
    grammar: str
    details: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))
        if not isinstance(self.timestamp, datetime) or self.timestamp.tzinfo is None:
            raise ValueError("WorkshopEvent.timestamp must be timezone-aware (UTC)")
        self.timestamp = self.timestamp.astimezone(timezone.utc)
        if not isinstance(self.stage, str) or not self.stage:
            raise ValueError("WorkshopEvent.stage must be a non-empty string")
        if not isinstance(self.status, str) or not self.status:
            raise ValueError("WorkshopEvent.status must be a non-empty string")
        if not isinstance(self.grammar, str) or not self.grammar:
            raise ValueError("WorkshopEvent.grammar must be a non-empty string")

    def model_dump(self, mode: str = "python") -> dict[str, Any]:
        payload = asdict(self)
        return _to_jsonable(payload) if mode == "json" else payload

    @classmethod
    def model_validate(cls, payload: dict[str, Any]) -> "WorkshopEvent":
        return cls(**payload)

    @classmethod
    def model_validate_json(cls, payload: str) -> "WorkshopEvent":
        return cls.model_validate(json.loads(payload))

    def model_dump_json(self) -> str:
        return json.dumps(
            self.model_dump(mode="json"),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    def to_jsonl(self) -> str:
        """Serialize event to a single-line JSONL record."""
        return self.model_dump_json().replace("\n", "\\n").replace("\r", "\\r")

    @classmethod
    def from_jsonl(cls, payload: str) -> "WorkshopEvent":
        """Deserialize event from one JSONL line."""
        return cls.model_validate_json(payload)
