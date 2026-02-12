"""Tests for CUE formatting and validity enforcement."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from confidantic.workshop.services import generate_workshop_schemas


@pytest.fixture
def sample_generated_cue_dir(tmp_path: Path) -> Path:
    """Generate and format CUE files using the service layer."""
    output_dir = tmp_path / "build" / "schemas" / "cue" / "python"
    generate_workshop_schemas(
        grammar="python",
        node_types_path=Path("tests/fixtures/python/node-types.json"),
        queries_dir=Path("tests/fixtures/python/queries"),
        output_dir=output_dir,
    )
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

    # Validate each CUE file individually (cue vet doesn't accept absolute directory paths)
    for cue_file in sorted(sample_generated_cue_dir.glob("*.cue")):
        result = subprocess.run(["cue", "vet", str(cue_file)], capture_output=True, text=True)
        assert result.returncode == 0, f"Validation failed for {cue_file}: {result.stderr}"
