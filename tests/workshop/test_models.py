from __future__ import annotations

from datetime import datetime, timezone

import pytest

from confidantic.workshop.models import (
    NodeType,
    NodeTypes,
    QueryCapture,
    QueryFile,
    WorkshopInput,
)


def test_node_type_validation() -> None:
    with pytest.raises(ValueError, match="non-empty string"):
        NodeType(type="", named=True)

    with pytest.raises(ValueError, match="boolean"):
        NodeType(type="identifier", named="yes")  # type: ignore[arg-type]


def test_query_capture_validation() -> None:
    with pytest.raises(ValueError, match="start with '@'"):
        QueryCapture(name="function")


def test_node_types_ordering_is_deterministic() -> None:
    payload = [
        {"type": "zeta", "named": True},
        {"type": "alpha", "named": True},
        {"type": "beta", "named": False},
    ]

    runs = [NodeTypes(nodes=payload) for _ in range(5)]
    ordered = [[node.type for node in item.nodes] for item in runs]

    assert all(item == ordered[0] for item in ordered)
    assert ordered[0] == ["alpha", "beta", "zeta"]


def test_query_file_capture_ordering_is_deterministic() -> None:
    captures = [
        {"name": "@z", "line": 3},
        {"name": "@a", "line": 10},
        {"name": "@a", "line": 2},
    ]

    query = QueryFile(
        query_type="highlights",
        file_path="queries/highlights.scm",
        content="(identifier) @a",
        captures=captures,
    )

    assert [(capture.name, capture.line) for capture in query.captures] == [
        ("@a", 2),
        ("@a", 10),
        ("@z", 3),
    ]


def test_workshop_input_orders_query_files_and_source_paths() -> None:
    workshop = WorkshopInput(
        grammar_name="python",
        node_types={"nodes": [{"type": "identifier", "named": True}]},
        query_files=[
            {
                "query_type": "tags",
                "file_path": "queries/tags.scm",
                "content": "(class_definition) @definition.class",
            },
            {
                "query_type": "highlights",
                "file_path": "queries/highlights.scm",
                "content": "(identifier) @variable",
            },
        ],
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        source_paths={"z": "z/path", "a": "a/path"},
    )

    assert [query.query_type for query in workshop.query_files] == ["highlights", "tags"]
    assert list(workshop.source_paths.keys()) == ["a", "z"]
