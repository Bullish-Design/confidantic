"""Tests for the JSONL loader."""

from pathlib import Path

import pytest
from pydantic import BaseModel

from confidantic.core.errors import JsonlValidationError
from confidantic.core.loader_jsonl import load_jsonl


class SimpleRecord(BaseModel):
    name: str
    value: int


class TestJsonlLoader:
    def test_valid_lines(self, tmp_path: Path):
        f = tmp_path / "data.jsonl"
        f.write_text(
            '{"name": "a", "value": 1}\n'
            '{"name": "b", "value": 2}\n'
        )
        result = load_jsonl(f, SimpleRecord)
        assert len(result.records) == 2
        assert len(result.warnings) == 0
        assert result.records[0].name == "a"
        assert result.records[1].value == 2

    def test_invalid_json_warns_and_skips(self, tmp_path: Path):
        f = tmp_path / "data.jsonl"
        f.write_text(
            '{"name": "a", "value": 1}\n'
            'not json\n'
            '{"name": "b", "value": 2}\n'
        )
        result = load_jsonl(f, SimpleRecord)
        assert len(result.records) == 2
        assert len(result.warnings) == 1
        assert result.warnings[0].line_number == 2
        assert "invalid JSON" in result.warnings[0].detail

    def test_validation_error_warns_and_skips(self, tmp_path: Path):
        f = tmp_path / "data.jsonl"
        f.write_text(
            '{"name": "a", "value": 1}\n'
            '{"name": "b"}\n'  # missing 'value'
        )
        result = load_jsonl(f, SimpleRecord)
        assert len(result.records) == 1
        assert len(result.warnings) == 1
        assert result.warnings[0].line_number == 2
        assert "validation error" in result.warnings[0].detail

    def test_empty_lines_ignored(self, tmp_path: Path):
        f = tmp_path / "data.jsonl"
        f.write_text(
            '\n'
            '{"name": "a", "value": 1}\n'
            '\n'
            '{"name": "b", "value": 2}\n'
            '\n'
        )
        result = load_jsonl(f, SimpleRecord)
        assert len(result.records) == 2
        assert len(result.warnings) == 0

    def test_strict_mode_raises(self, tmp_path: Path):
        f = tmp_path / "data.jsonl"
        f.write_text(
            '{"name": "a", "value": 1}\n'
            'bad line\n'
        )
        with pytest.raises(JsonlValidationError) as exc_info:
            load_jsonl(f, SimpleRecord, strict=True)
        assert len(exc_info.value.warnings) == 1

    def test_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            load_jsonl(tmp_path / "missing.jsonl", SimpleRecord)

    def test_line_numbering_is_one_based(self, tmp_path: Path):
        f = tmp_path / "data.jsonl"
        f.write_text(
            'bad1\n'
            '{"name": "ok", "value": 1}\n'
            'bad3\n'
        )
        result = load_jsonl(f, SimpleRecord)
        assert result.warnings[0].line_number == 1
        assert result.warnings[1].line_number == 3

    def test_record_dicts_property(self, tmp_path: Path):
        f = tmp_path / "data.jsonl"
        f.write_text('{"name": "a", "value": 1}\n')
        result = load_jsonl(f, SimpleRecord)
        dicts = result.record_dicts
        assert dicts == [{"name": "a", "value": 1}]
