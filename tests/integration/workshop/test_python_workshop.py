"""End-to-end workshop integration for Python grammar."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from confidantic.workshop.doctor import WorkshopDoctor
from confidantic.workshop.logging import WorkshopLogReader, WorkshopLogger
from confidantic.workshop.services import generate_workshop_schemas


def test_python_workshop_end_to_end(tmp_path: Path) -> None:
    if shutil.which("cue") is None:
        pytest.skip("cue binary not available")

    fixtures = Path("tests/fixtures/python")
    output_dir = tmp_path / "build" / "schemas" / "cue" / "python"

    # Use service layer to generate and format files
    result = generate_workshop_schemas(
        grammar="python",
        node_types_path=fixtures / "node-types.json",
        queries_dir=fixtures / "queries",
        output_dir=output_dir,
    )
    assert len(result.generated_files) == 3

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
    logger.log_event(stage="generate", status="success", grammar="python", artifact_paths=list(result.generated_files))
    assert len(WorkshopLogReader(log_path=log_file).filter_by_grammar("python")) == 1


def test_workflow_cli_group_is_available() -> None:
    from confidantic.cli import app

    command_names = [command.name for command in app.registered_commands]
    group_names = [group.name for group in app.registered_groups]
    assert "workflow" in group_names
