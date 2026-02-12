"""Golden snapshot tests for deterministic workshop generation."""

from __future__ import annotations

from pathlib import Path
import re

from confidantic.workshop.generator import CueGenerator
from confidantic.workshop.loaders import load_workshop_input


def normalize_cue(content: str) -> str:
    content = re.sub(r'generated_at: "[^"]+"', 'generated_at: "NORMALIZED"', content)
    content = re.sub(r'fingerprint: "[a-f0-9]+"', 'fingerprint: "NORMALIZED"', content)
    return content


def _load_input():
    return load_workshop_input(
        grammar_name="python",
        node_types_path=Path("tests/fixtures/python/node-types.json"),
        queries_dir=Path("tests/fixtures/python/queries"),
    )


def test_python_node_types_matches_golden(tmp_path: Path) -> None:
    workshop_input = _load_input()
    output_dir = tmp_path / "build" / "schemas" / "cue" / "python"

    generated = CueGenerator(workshop_input).generate(output_dir)
    assert generated

    golden_dir = Path("tests/fixtures/golden/python")
    for output_file in sorted(output_dir.glob("*.cue")):
        golden_file = golden_dir / output_file.name
        assert golden_file.exists(), f"Missing golden file: {golden_file}"
        assert normalize_cue(output_file.read_text()) == normalize_cue(golden_file.read_text())


def test_generation_is_deterministic_across_runs(tmp_path: Path) -> None:
    workshop_input = _load_input()

    runs: list[dict[str, str]] = []
    for idx in range(3):
        run_dir = tmp_path / "build" / f"run_{idx}" / "schemas" / "cue" / "python"
        CueGenerator(workshop_input).generate(run_dir)
        runs.append({p.name: normalize_cue(p.read_text()) for p in sorted(run_dir.glob("*.cue"))})

    assert runs[1] == runs[0]
    assert runs[2] == runs[0]
