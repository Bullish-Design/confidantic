"""Tests for the TOML loader."""

import textwrap
from pathlib import Path

import pytest
from pydantic import BaseModel

from confidantic.core.errors import TomlLoadError
from confidantic.core.loader_toml import (
    load_toml_as_dict,
    load_toml_raw,
    load_toml_validated,
)


class SimpleModel(BaseModel):
    name: str
    count: int = 0


class StrictModel(BaseModel):
    class Config:
        extra = "forbid"

    name: str


class TestLoadTomlRaw:
    def test_valid_toml(self, tmp_path: Path):
        f = tmp_path / "test.toml"
        f.write_text('name = "hello"\ncount = 42\n')
        result = load_toml_raw(f)
        assert result == {"name": "hello", "count": 42}

    def test_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(TomlLoadError, match="does not exist"):
            load_toml_raw(tmp_path / "missing.toml")

    def test_invalid_toml_raises(self, tmp_path: Path):
        f = tmp_path / "bad.toml"
        f.write_text("not valid toml [[[")
        with pytest.raises(TomlLoadError, match="TOML parse error"):
            load_toml_raw(f)


class TestLoadTomlValidated:
    def test_valid_data(self, tmp_path: Path):
        f = tmp_path / "test.toml"
        f.write_text('name = "test"\ncount = 5\n')
        result = load_toml_validated(f, SimpleModel)
        assert result.name == "test"
        assert result.count == 5

    def test_defaults_applied(self, tmp_path: Path):
        f = tmp_path / "test.toml"
        f.write_text('name = "test"\n')
        result = load_toml_validated(f, SimpleModel)
        assert result.count == 0

    def test_validation_error_includes_path(self, tmp_path: Path):
        f = tmp_path / "test.toml"
        f.write_text('count = 5\n')  # missing required 'name'
        with pytest.raises(TomlLoadError) as exc_info:
            load_toml_validated(f, SimpleModel)
        assert str(f) in str(exc_info.value)

    def test_type_error_in_validation(self, tmp_path: Path):
        f = tmp_path / "test.toml"
        f.write_text('name = 123\n')  # name should be str
        # Pydantic strict mode rejects int for str field
        with pytest.raises(TomlLoadError, match="name"):
            load_toml_validated(f, SimpleModel)


class TestLoadTomlAsDict:
    def test_returns_plain_dict(self, tmp_path: Path):
        f = tmp_path / "test.toml"
        f.write_text(textwrap.dedent("""\
            [section]
            key = "value"
            num = 42
        """))
        result = load_toml_as_dict(f)
        assert result == {"section": {"key": "value", "num": 42}}
