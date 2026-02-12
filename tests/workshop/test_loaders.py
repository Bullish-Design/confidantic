from __future__ import annotations

from pathlib import Path

import pytest

from confidantic.workshop.loaders import (
    append_jsonl_record,
    discover_query_files,
    load_node_types,
    load_query_file,
    read_jsonl_records,
)


FIXTURES = Path("tests/fixtures/python")


def test_load_node_types_valid_fixture() -> None:
    node_types = load_node_types(FIXTURES / "node-types.json")

    assert [node.type for node in node_types.nodes] == [
        "expression_statement",
        "identifier",
        "module",
    ]


def test_load_node_types_malformed_has_file_line_and_column() -> None:
    with pytest.raises(ValueError, match=r"node-types-malformed\.json: line \d+, column \d+"):
        load_node_types(FIXTURES / "malformed" / "node-types-malformed.json")


def test_load_node_types_missing_file() -> None:
    with pytest.raises(ValueError, match="Unable to read node-types file"):
        load_node_types(FIXTURES / "does-not-exist.json")


def test_load_query_file_valid_fixture_extracts_captures() -> None:
    query = load_query_file(FIXTURES / "queries" / "highlights.scm", query_type="highlights")

    assert query.query_type == "highlights"
    assert {capture.name for capture in query.captures} >= {
        "@function.definition",
        "@type.definition",
        "@variable",
    }


def test_load_query_file_malformed_has_file_line_and_column() -> None:
    with pytest.raises(ValueError, match=r"highlights-malformed\.scm: line \d+, column \d+"):
        load_query_file(
            FIXTURES / "malformed" / "queries" / "highlights-malformed.scm",
            query_type="highlights",
        )


def test_discover_query_files_missing_required() -> None:
    with pytest.raises(ValueError, match=r"Missing required query file\(s\)"):
        discover_query_files(FIXTURES / "queries", required=["highlights.scm", "locals.scm"])


def test_jsonl_roundtrip_and_invalid_line_warning(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    append_jsonl_record({"stage": "load", "status": "success"}, path)
    path.write_text(path.read_text() + "{bad json}\n")

    with pytest.warns(UserWarning, match=r"events\.jsonl at line 2"):
        records = read_jsonl_records(path)

    assert records == [{"stage": "load", "status": "success"}]


def test_jsonl_strict_mode_aggregates_failures(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text('{"ok": 1}\n{bad json}\n[]\n', encoding="utf-8")

    with pytest.raises(ValueError, match=r"Invalid JSONL lines encountered \(2\)"):
        read_jsonl_records(path, strict=True)
