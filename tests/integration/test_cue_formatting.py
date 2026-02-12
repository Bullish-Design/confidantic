"""Tests for CUE formatting and validity enforcement."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from confidantic.workshop.generator import CueGenerator
from confidantic.workshop.loaders import load_workshop_input


@pytest.fixture
def sample_generated_cue_dir(tmp_path: Path) -> Path:
    workshop_input = load_workshop_input(
        grammar_name="python",
        node_types_path=Path("tests/fixtures/python/node-types.json"),
        queries_dir=Path("tests/fixtures/python/queries"),
    )
    output_dir = tmp_path / "build" / "schemas" / "cue" / "python"
    CueGenerator(workshop_input).generate(output_dir)
    return output_dir


def test_all_generated_cue_is_formatted(sample_generated_cue_dir: Path) -> None:
    if shutil.which("cue") is None:
        pytest.skip("cue binary not found")

    for cue_file in sample_generated_cue_dir.glob("*.cue"):
        result = subprocess.run(["cue", "fmt", "--check", str(cue_file)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr


def test_all_generated_cue_is_valid(sample_generated_cue_dir: Path) -> None:
    if shutil.which("cue") is None:
        pytest.skip("cue binary not found")

    result = subprocess.run(["cue", "vet", str(sample_generated_cue_dir)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
