from __future__ import annotations

from pathlib import Path

from confidantic.workshop.generator import CueGenerator
from confidantic.workshop.loaders import load_workshop_input


def test_golden_snapshot_match(tmp_path: Path) -> None:
    workshop_input = load_workshop_input(
        grammar_name="python",
        node_types_path=Path("tests/fixtures/python/node-types.json"),
        queries_dir=Path("tests/fixtures/python/queries"),
    )
    output_dir = tmp_path / "build/schemas/cue/python"

    generator = CueGenerator(workshop_input)
    generated_files = generator.generate(output_dir)

    golden_dir = Path("tests/fixtures/golden/python")
    assert sorted(path.name for path in generated_files) == sorted(path.name for path in golden_dir.glob("*.cue"))
    for generated_file in generated_files:
        golden_file = golden_dir / generated_file.name
        assert generated_file.read_text(encoding="utf-8") == golden_file.read_text(encoding="utf-8")
