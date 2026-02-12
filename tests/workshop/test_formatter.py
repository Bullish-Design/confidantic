from __future__ import annotations

from pathlib import Path
import subprocess

from confidantic.cue import formatter
from confidantic.cue.formatter import format_cue_directory, format_cue_file, validate_cue_file


def test_validate_cue_file_reports_missing_cue_binary(tmp_path: Path, monkeypatch) -> None:
    cue_file = tmp_path / "build/schemas/cue/test/sample.cue"
    cue_file.parent.mkdir(parents=True, exist_ok=True)
    cue_file.write_text('package test\n#Value: "x"\n', encoding='utf-8')

    def _raise_missing_binary(*args, **kwargs):
        raise FileNotFoundError("cue")

    monkeypatch.setattr(formatter.subprocess, "run", _raise_missing_binary)

    success, error = validate_cue_file(cue_file)
    assert success is False
    assert error is not None
    assert "`cue` binary not found on PATH" in error
    assert "cue vet" in error


def test_validate_cue_file_reports_vet_failure_output(tmp_path: Path, monkeypatch) -> None:
    cue_file = tmp_path / "build/schemas/cue/test/sample.cue"
    cue_file.parent.mkdir(parents=True, exist_ok=True)
    cue_file.write_text('package test\n#Value: "x"\n', encoding='utf-8')

    def _raise_vet_failure(*args, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=["cue", "vet", str(cue_file)],
            stderr="schema mismatch",
        )

    monkeypatch.setattr(formatter.subprocess, "run", _raise_vet_failure)

    success, error = validate_cue_file(cue_file)
    assert success is False
    assert error == f"Validation failed for {cue_file}: schema mismatch"


def test_format_cue_directory_reports_per_file(tmp_path: Path) -> None:
    root = tmp_path / "build/schemas/cue/test"
    root.mkdir(parents=True, exist_ok=True)
    (root / "a.cue").write_text('package test\n#A: "x"\n', encoding='utf-8')
    (root / "b.cue").write_text('package test\n#B: "y"\n', encoding='utf-8')

    results = format_cue_directory(root)
    assert sorted(path.name for path in results) == ["a.cue", "b.cue"]


def test_format_cue_file_requires_existing_file(tmp_path: Path) -> None:
    missing = tmp_path / "build/schemas/cue/test/missing.cue"

    try:
        format_cue_file(missing)
    except FileNotFoundError:
        assert True
    else:
        assert False, "Expected FileNotFoundError"
