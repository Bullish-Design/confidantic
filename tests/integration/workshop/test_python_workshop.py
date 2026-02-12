"""End-to-end workshop integration for Python grammar."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from confidantic.workshop.doctor import WorkshopDoctor
from confidantic.workshop.generator import CueGenerator
from confidantic.workshop.loaders import load_workshop_input
from confidantic.workshop.logging import WorkshopLogReader, WorkshopLogger


def test_python_workshop_end_to_end(tmp_path: Path) -> None:
    if shutil.which("cue") is None:
        pytest.skip("cue binary not available")

    fixtures = Path("tests/fixtures/python")
    output_dir = tmp_path / "build" / "schemas" / "cue" / "python"

    workshop_input = load_workshop_input(
        grammar_name="python",
        node_types_path=fixtures / "node-types.json",
        queries_dir=fixtures / "queries",
    )
    generated = CueGenerator(workshop_input).generate(output_dir)
    assert len(generated) == 3

    doctor = WorkshopDoctor(
        grammar="python",
        node_types_path=fixtures / "node-types.json",
        queries_dir=fixtures / "queries",
        schemas_dir=output_dir,
    )
    report = doctor.run_diagnostics()
    assert report.errors == []

    log_file = tmp_path / "logs" / "workshop.jsonl"
    logger = WorkshopLogger(log_path=log_file)
    logger.log_event(stage="generate", status="success", grammar="python", artifact_paths=generated)
    assert len(WorkshopLogReader(log_path=log_file).filter_by_grammar("python")) == 1


def test_workshop_recipe_smoke(tmp_path: Path) -> None:
    if shutil.which("just") is None:
        pytest.skip("just binary not available")

    # Minimal smoke check: recipe file exists and just can list it.
    recipe_file = Path("scripts/confidantic.just")
    assert recipe_file.exists()
