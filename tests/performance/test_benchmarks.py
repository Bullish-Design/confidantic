"""Performance sanity checks for workshop operations."""

from __future__ import annotations

import time
from pathlib import Path

from confidantic.workshop.generator import CueGenerator
from confidantic.workshop.loaders import load_workshop_input


def test_load_python_fixture_performance() -> None:
    start = time.perf_counter()
    workshop_input = load_workshop_input(
        grammar_name="python",
        node_types_path=Path("tests/fixtures/python/node-types.json"),
        queries_dir=Path("tests/fixtures/python/queries"),
    )
    elapsed = time.perf_counter() - start

    assert elapsed < 2.0
    assert len(workshop_input.node_types.nodes) > 0


def test_generate_python_fixture_performance(tmp_path: Path) -> None:
    workshop_input = load_workshop_input(
        grammar_name="python",
        node_types_path=Path("tests/fixtures/python/node-types.json"),
        queries_dir=Path("tests/fixtures/python/queries"),
    )
    start = time.perf_counter()
    CueGenerator(workshop_input).generate(tmp_path / "build" / "schemas" / "cue" / "python")
    elapsed = time.perf_counter() - start

    assert elapsed < 5.0
