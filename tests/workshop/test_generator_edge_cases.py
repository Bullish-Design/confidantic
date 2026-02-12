from __future__ import annotations

from pathlib import Path

import pytest

from confidantic.workshop.generator import CueGenerator
from confidantic.workshop.models import NodeTypes, QueryFile, WorkshopInput


def test_empty_inputs_generate_valid_files(tmp_path: Path) -> None:
    workshop_input = WorkshopInput(
        grammar_name="empty",
        node_types=NodeTypes(nodes=[]),
        query_files=[],
        source_paths={},
    )

    output_dir = tmp_path / "build/schemas/cue/empty"
    generated = CueGenerator(workshop_input).generate(output_dir)
    assert len(generated) == 3


def test_special_characters_in_node_names(tmp_path: Path) -> None:
    workshop_input = WorkshopInput(
        grammar_name="special",
        node_types=NodeTypes(
            nodes=[
                {"type": "with-hyphen", "named": True},
                {"type": "with space", "named": False},
                {"type": "9leading", "named": True},
            ]
        ),
        query_files=[],
    )
    output_dir = tmp_path / "build/schemas/cue/special"

    node_types_file = [path for path in CueGenerator(workshop_input).generate(output_dir) if path.name == "node_types.cue"][0]
    content = node_types_file.read_text(encoding="utf-8")
    assert "#with_hyphen" in content
    assert "#with_space" in content
    assert "#n_9leading" in content


def test_output_directory_must_include_build_path(tmp_path: Path) -> None:
    workshop_input = WorkshopInput(
        grammar_name="test",
        node_types=NodeTypes(nodes=[{"type": "identifier", "named": True}]),
        query_files=[
            QueryFile(
                query_type="highlights",
                file_path=Path("queries/highlights.scm"),
                content="(identifier) @variable",
                captures=[],
            )
        ],
    )

    with pytest.raises(ValueError, match="inside build"):
        CueGenerator(workshop_input).generate(tmp_path / "output")
