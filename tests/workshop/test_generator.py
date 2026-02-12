from __future__ import annotations

from pathlib import Path

from confidantic.workshop.generator import CueGenerator
from confidantic.workshop.loaders import load_workshop_input


def _load_python_workshop_input() -> object:
    return load_workshop_input(
        grammar_name="python",
        node_types_path=Path("tests/fixtures/python/node-types.json"),
        queries_dir=Path("tests/fixtures/python/queries"),
    )


def test_generate_from_workshop_input(tmp_path: Path) -> None:
    output_dir = tmp_path / "build/schemas/cue/python"
    generator = CueGenerator(_load_python_workshop_input())

    generated_files = generator.generate(output_dir)

    assert [path.name for path in generated_files] == ["captures.cue", "metadata.cue", "node_types.cue"]
    assert all(path.exists() for path in generated_files)
    for path in generated_files:
        content = path.read_text(encoding="utf-8")
        assert content.startswith("//")
        assert "package python" in content


def test_deterministic_generation(tmp_path: Path) -> None:
    workshop_input = _load_python_workshop_input()
    outputs: list[dict[str, bytes]] = []

    for idx in range(3):
        output_dir = tmp_path / f"run_{idx}" / "build/schemas/cue/python"
        generator = CueGenerator(workshop_input)
        files = generator.generate(output_dir)
        outputs.append({file.name: file.read_bytes() for file in files})

    assert outputs[0] == outputs[1] == outputs[2]


def test_provenance_comments_include_sources(tmp_path: Path) -> None:
    output_dir = tmp_path / "build/schemas/cue/python"
    generator = CueGenerator(_load_python_workshop_input())

    generated_files = generator.generate(output_dir)
    for path in generated_files:
        content = path.read_text(encoding="utf-8")
        assert "// Generated from:" in content or "// Grammar metadata" in content
