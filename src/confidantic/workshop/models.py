"""Phase 1 workshop models for Tree-sitter artifact ingestion."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, ClassVar


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


@dataclass(slots=True)
class NodeType:
    """A single node-type entry from Tree-sitter's ``node-types.json``."""

    model_fields: ClassVar[dict[str, Any]] = {"type": str, "named": bool}

    type: str
    named: bool
    fields: dict[str, object] = field(default_factory=dict)
    children: dict[str, object] | None = None
    subtypes: list[dict[str, object]] = field(default_factory=list)


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
        self.nodes = sorted(coerced, key=lambda n: (n.type, 0 if n.named else 1))

    def model_dump(self, mode: str = "python") -> dict[str, Any]:
        return {"nodes": [_to_jsonable(asdict(node)) for node in self.nodes]}


@dataclass(slots=True)
class QueryCapture:
    """A capture token parsed from a Tree-sitter query file."""

    model_fields: ClassVar[dict[str, Any]] = {"name": str}

    name: str
    pattern: str | None = None


@dataclass(slots=True)
class QueryFile:
    """A deterministic representation of one ``.scm`` query file."""

    model_fields: ClassVar[dict[str, Any]] = {"query_type": str, "file_path": Path}

    query_type: str
    file_path: Path
    content: str
    captures: list[QueryCapture | dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.file_path = Path(self.file_path)
        normalized: list[QueryCapture] = []
        for capture in self.captures:
            if isinstance(capture, QueryCapture):
                normalized.append(capture)
            else:
                normalized.append(QueryCapture(**capture))
        self.captures = sorted(normalized, key=lambda c: c.name)


@dataclass(slots=True)
class WorkshopInput:
    """Workshop source inputs for deterministic generation."""

    model_fields: ClassVar[dict[str, Any]] = {
        "grammar_name": str,
        "node_types": NodeTypes,
        "query_files": list,
    }

    grammar_name: str
    node_types: NodeTypes | dict[str, Any]
    query_files: list[QueryFile | dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.node_types, NodeTypes):
            self.node_types = NodeTypes(**self.node_types)

        normalized: list[QueryFile] = []
        for query_file in self.query_files:
            if isinstance(query_file, QueryFile):
                normalized.append(query_file)
            else:
                normalized.append(QueryFile(**query_file))
        self.query_files = sorted(normalized, key=lambda q: q.file_path.name)

    def model_dump(self, mode: str = "python") -> dict[str, Any]:
        payload = {
            "grammar_name": self.grammar_name,
            "node_types": self.node_types.model_dump(mode=mode),
            "query_files": [_to_jsonable(asdict(query_file)) for query_file in self.query_files],
        }
        return _to_jsonable(payload) if mode == "json" else payload

    def fingerprint(self) -> str:
        """Return a deterministic fingerprint of normalized workshop input."""
        normalized = self.model_dump(mode="json")
        payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
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
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=timezone.utc)

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
        return json.dumps(self.model_dump(mode="json"), sort_keys=True)

    def to_jsonl(self) -> str:
        """Serialize event to a single-line JSONL record."""
        return self.model_dump_json()
