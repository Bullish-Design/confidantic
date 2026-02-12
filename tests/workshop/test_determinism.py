from __future__ import annotations

from pathlib import Path

from confidantic.workshop.loaders import discover_query_files, load_workshop_input


def test_discover_query_files_is_stable_over_repeated_runs() -> None:
    queries_dir = Path("tests/fixtures/python/queries")

    discovered = [discover_query_files(queries_dir) for _ in range(10)]
    names = [[item.name for item in run] for run in discovered]

    assert all(run == names[0] for run in names)
    assert names[0] == ["highlights.scm", "tags.scm"]


def test_fingerprint_stability_over_10_runs() -> None:
    fingerprints = []

    for _ in range(10):
        workshop = load_workshop_input(
            grammar_name="python",
            node_types_path=Path("tests/fixtures/python/node-types.json"),
            queries_dir=Path("tests/fixtures/python/queries"),
        )
        fingerprints.append(workshop.fingerprint())

    assert len(set(fingerprints)) == 1
