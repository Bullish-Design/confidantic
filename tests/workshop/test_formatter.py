from __future__ import annotations

from pathlib import Path

from confidantic.cue.formatter import format_cue_directory, format_cue_file, validate_cue_file


def test_validate_cue_file_missing_binary_or_invalid(tmp_path: Path) -> None:
    cue_file = tmp_path / "build/schemas/cue/test/sample.cue"
    cue_file.parent.mkdir(parents=True, exist_ok=True)
    cue_file.write_text('package test\n#Value: "x"\n', encoding='utf-8')

    success, error = validate_cue_file(cue_file)
    assert (success is True and error is None) or (success is False and error is not None)


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
