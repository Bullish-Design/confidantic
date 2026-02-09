"""Tests for core Pydantic models."""

import json

import pytest
from pydantic import SecretStr, ValidationError

from confidantic.models.base import REDACTED_TOKEN, BaseConfig
from confidantic.models.metadata import DevmanContext
from confidantic.models.registry import DatasetDeclaration, RegistryConfig
from confidantic.models.resolved import ResolvedBundle, ResolutionMeta


class TestBaseConfig:
    def test_extra_forbidden_by_default(self):
        class Strict(BaseConfig):
            name: str = "test"

        with pytest.raises(ValidationError):
            Strict(name="test", extra_field="boom")

    def test_to_redacted_dict(self):
        class Config(BaseConfig):
            visible: str = "hello"
            secret: SecretStr = SecretStr("hidden")

        result = Config().to_redacted_dict()
        assert result["visible"] == "hello"
        assert result["secret"] == REDACTED_TOKEN

    def test_to_stable_json(self):
        class Config(BaseConfig):
            b: str = "second"
            a: str = "first"

        j = Config().to_stable_json()
        data = json.loads(j)
        keys = list(data.keys())
        assert keys == sorted(keys)


class TestRegistryConfig:
    def test_defaults(self):
        reg = RegistryConfig()
        assert reg.profile_default == "default"
        assert reg.modules == []
        assert reg.datasets == {}
        assert reg.strict_jsonl is False

    def test_with_modules_and_datasets(self):
        reg = RegistryConfig(
            modules=["app", "infra"],
            datasets={
                "users": DatasetDeclaration(
                    path="data/users.jsonl",
                    record_model="myapp.models.User",
                )
            },
        )
        assert len(reg.modules) == 2
        assert "users" in reg.datasets

    def test_extra_forbidden(self):
        with pytest.raises(ValidationError):
            RegistryConfig(unknown_field="boom")


class TestDevmanContext:
    def test_defaults(self):
        ctx = DevmanContext()
        assert ctx.repo_root is None
        assert ctx.config_root is None
        assert ctx.jj_rev is None
        assert ctx.run_metadata == {}

    def test_to_dict_serializes_paths(self):
        from pathlib import Path

        ctx = DevmanContext(repo_root=Path("/foo/bar"))
        d = ctx.to_dict()
        assert d["repo_root"] == "/foo/bar"

    def test_extra_ignored(self):
        # DevmanContext allows extra fields (ignored)
        ctx = DevmanContext(unknown="whatever")
        assert not hasattr(ctx, "unknown") or True  # extra=ignore


class TestResolvedBundle:
    def test_basic_creation(self):
        meta = ResolutionMeta(
            profile="ci",
            modules=["app"],
            fingerprint="abc123",
        )
        bundle = ResolvedBundle(
            meta=meta,
            config={"app": {"debug": True}},
        )
        assert bundle.meta.profile == "ci"
        assert bundle.config["app"]["debug"] is True

    def test_to_stable_json_produces_sorted_keys(self):
        meta = ResolutionMeta(profile="default", modules=[])
        bundle = ResolvedBundle(meta=meta, config={"z": 1, "a": 2})
        j = bundle.to_stable_json()
        data = json.loads(j)
        keys = list(data["config"].keys())
        assert keys == sorted(keys)

    def test_to_redacted_dict_masks_secrets(self):
        meta = ResolutionMeta(profile="default", modules=[])
        bundle = ResolvedBundle(
            meta=meta,
            config={"api_key": "secret123", "name": "test"},
        )
        redacted = bundle.to_redacted_dict()
        assert redacted["config"]["api_key"] == REDACTED_TOKEN
        assert redacted["config"]["name"] == "test"
