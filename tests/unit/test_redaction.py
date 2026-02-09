"""Tests for the redaction engine."""

from pydantic import Field, SecretStr

from confidantic.core.redaction import redact_model
from confidantic.models.base import REDACTED_TOKEN, BaseConfig


class TestRedaction:
    def test_secret_str_redacted(self):
        class Config(BaseConfig):
            model_config = {"extra": "forbid"}
            api_key: SecretStr = SecretStr("hunter2")

        result = redact_model(Config())
        assert result["api_key"] == REDACTED_TOKEN

    def test_redact_flag_on_field(self):
        class Config(BaseConfig):
            model_config = {"extra": "forbid"}
            password: str = Field(
                default="secret123",
                json_schema_extra={"redact": True},
            )

        result = redact_model(Config())
        assert result["password"] == REDACTED_TOKEN

    def test_non_secret_field_not_redacted(self):
        class Config(BaseConfig):
            model_config = {"extra": "forbid"}
            name: str = "public"

        result = redact_model(Config())
        assert result["name"] == "public"

    def test_nested_model_redaction(self):
        class Inner(BaseConfig):
            model_config = {"extra": "forbid"}
            token: SecretStr = SecretStr("abc")
            label: str = "visible"

        class Outer(BaseConfig):
            model_config = {"extra": "forbid"}
            inner: Inner = Field(default_factory=Inner)

        result = redact_model(Outer())
        assert result["inner"]["token"] == REDACTED_TOKEN
        assert result["inner"]["label"] == "visible"

    def test_list_of_models_redaction(self):
        class Item(BaseConfig):
            model_config = {"extra": "forbid"}
            key: SecretStr = SecretStr("x")
            name: str = "item"

        class Config(BaseConfig):
            model_config = {"extra": "forbid"}
            items: list[Item] = Field(
                default_factory=lambda: [Item(), Item(name="other")]
            )

        result = redact_model(Config())
        for item in result["items"]:
            assert item["key"] == REDACTED_TOKEN
            assert item["name"] in ("item", "other")

    def test_dict_values_not_schema_redacted(self):
        class Config(BaseConfig):
            model_config = {"extra": "forbid"}
            metadata: dict = Field(default_factory=lambda: {"x": 1})

        result = redact_model(Config())
        assert result["metadata"] == {"x": 1}

    def test_base_config_to_redacted_dict(self):
        class Config(BaseConfig):
            model_config = {"extra": "forbid"}
            secret: SecretStr = SecretStr("hidden")
            visible: str = "shown"

        config = Config()
        result = config.to_redacted_dict()
        assert result["secret"] == REDACTED_TOKEN
        assert result["visible"] == "shown"
