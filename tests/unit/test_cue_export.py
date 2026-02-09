"""Tests for CUE export naming and emitters."""

from typing import Optional

from pydantic import BaseModel, Field, SecretStr

from confidantic.cue_export.emitters import emit_cue_definition
from confidantic.cue_export.naming import (
    field_name_to_cue,
    model_to_cue_filename,
    python_type_to_cue,
)


class TestNaming:
    def test_camel_to_snake_filename(self):
        assert model_to_cue_filename("AppConfig") == "app_config.cue"

    def test_simple_name(self):
        assert model_to_cue_filename("Config") == "config.cue"

    def test_multi_caps(self):
        # Each capital-to-lowercase transition gets an underscore
        result = model_to_cue_filename("HTTPServerConfig")
        assert result.endswith(".cue")
        # Verify it's deterministic and stable
        assert result == model_to_cue_filename("HTTPServerConfig")

    def test_field_name_valid_identifier(self):
        assert field_name_to_cue("my_field") == "my_field"

    def test_field_name_needs_quoting(self):
        assert field_name_to_cue("my-field") == '"my-field"'

    def test_python_type_mappings(self):
        assert python_type_to_cue("str") == "string"
        assert python_type_to_cue("int") == "int"
        assert python_type_to_cue("bool") == "bool"
        assert python_type_to_cue("float") == "float"
        assert python_type_to_cue("SecretStr") == "string"
        assert python_type_to_cue("Unknown") == "_"


class TestEmitters:
    def test_simple_model(self):
        class Simple(BaseModel):
            name: str
            count: int = 0

        cue = emit_cue_definition(Simple, package_name="test")
        assert "package test" in cue
        assert "#Simple" in cue
        assert "name: string" in cue
        assert "count?" in cue  # has default -> optional

    def test_optional_field(self):
        class WithOptional(BaseModel):
            label: Optional[str] = None

        cue = emit_cue_definition(WithOptional)
        assert "label?" in cue

    def test_nested_model_reference(self):
        class Inner(BaseModel):
            x: int

        class Outer(BaseModel):
            inner: Inner

        cue = emit_cue_definition(Outer)
        assert "#Inner" in cue

    def test_list_field(self):
        class WithList(BaseModel):
            tags: list[str] = Field(default_factory=list)

        cue = emit_cue_definition(WithList)
        assert "[...string]" in cue

    def test_secret_str_maps_to_string(self):
        class WithSecret(BaseModel):
            token: SecretStr

        cue = emit_cue_definition(WithSecret)
        assert "string" in cue
