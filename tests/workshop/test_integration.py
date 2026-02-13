from __future__ import annotations

from pathlib import Path

from confidantic.workshop.loaders import load_workshop_input


def test_workshop_input_loads_python_fixtures() -> None:
    workshop = load_workshop_input(
        grammar_name="python",
        node_types_path=Path("tests/fixtures/python/node-types.json"),
        queries_dir=Path("tests/fixtures/python/queries"),
    )

    assert workshop.grammar_name == "python"
    assert [node.type for node in workshop.node_types.nodes] == [
        "expression_statement",
        "identifier",
        "module",
    ]
    assert [query.query_type for query in workshop.query_files] == ["highlights", "tags"]


def test_fingerprint_is_stable_across_repeated_loads() -> None:
    fingerprints = [
        load_workshop_input(
            grammar_name="python",
            node_types_path=Path("tests/fixtures/python/node-types.json"),
            queries_dir=Path("tests/fixtures/python/queries"),
        ).fingerprint()
        for _ in range(10)
    ]

    assert len(set(fingerprints)) == 1
