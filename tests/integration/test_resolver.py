"""Integration tests for the resolver pipeline.

Creates realistic fixture trees and validates the full resolution flow.
"""

import json
import os
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from confidantic.core.errors import (
    ConfigRootNotFoundError,
    ModuleNotFoundError_,
    ProfileNotFoundError,
    RegistryNotFoundError,
)
from confidantic.core.resolver import resolve
from confidantic.core.snapshot import build_snapshot, snapshot_fingerprint


def _create_config_tree(root: Path, *, registry: str, **extra_files: str) -> Path:
    """Create a .devman/.config directory tree for testing."""
    config_root = root / ".devman" / ".config"
    config_root.mkdir(parents=True)

    (config_root / "confidantic.toml").write_text(registry)

    for rel_path, content in extra_files.items():
        p = config_root / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)

    return config_root


class TestResolverBasic:
    def test_minimal_resolution(self, tmp_path: Path):
        """Resolve with just a registry, no modules/profiles/datasets."""
        config_root = _create_config_tree(
            tmp_path,
            registry='profile_default = "default"\nmodules = []\n',
        )

        bundle = resolve(config_root=config_root)
        assert bundle.meta.profile == "default"
        assert bundle.meta.modules == []
        assert bundle.config == {}
        assert bundle.meta.fingerprint != ""

    def test_profile_overlay(self, tmp_path: Path):
        """Profile overlay merges into config."""
        config_root = _create_config_tree(
            tmp_path,
            registry='profile_default = "default"\nmodules = []\n',
            **{
                "profiles/default.toml": textwrap.dedent("""\
                    [app]
                    debug = true
                    name = "myapp"
                """),
            },
        )

        bundle = resolve(config_root=config_root)
        assert bundle.config["app"]["debug"] is True
        assert bundle.config["app"]["name"] == "myapp"

    def test_module_loading_in_order(self, tmp_path: Path):
        """Modules load and merge in declared order."""
        config_root = _create_config_tree(
            tmp_path,
            registry='profile_default = "default"\nmodules = ["base", "override"]\n',
            **{
                "modules/base.toml": textwrap.dedent("""\
                    [settings]
                    level = "info"
                    feature = "old"
                """),
                "modules/override.toml": textwrap.dedent("""\
                    [settings]
                    feature = "new"
                    extra = true
                """),
            },
        )

        bundle = resolve(config_root=config_root)
        # base.level retained, base.feature overridden by override
        assert bundle.config["settings"]["level"] == "info"
        assert bundle.config["settings"]["feature"] == "new"
        assert bundle.config["settings"]["extra"] is True

    def test_profile_plus_modules(self, tmp_path: Path):
        """Profile and modules merge together correctly."""
        config_root = _create_config_tree(
            tmp_path,
            registry='profile_default = "ci"\nmodules = ["app"]\n',
            **{
                "profiles/ci.toml": textwrap.dedent("""\
                    [env]
                    stage = "ci"
                """),
                "modules/app.toml": textwrap.dedent("""\
                    [env]
                    app_name = "myservice"
                """),
            },
        )

        bundle = resolve(config_root=config_root)
        assert bundle.meta.profile == "ci"
        assert bundle.config["env"]["stage"] == "ci"
        assert bundle.config["env"]["app_name"] == "myservice"

    def test_explicit_profile_overrides_default(self, tmp_path: Path):
        """Explicit profile arg takes precedence over registry default."""
        config_root = _create_config_tree(
            tmp_path,
            registry='profile_default = "default"\nmodules = []\n',
            **{
                "profiles/default.toml": "[app]\nmode = 'default'\n",
                "profiles/staging.toml": "[app]\nmode = 'staging'\n",
            },
        )

        bundle = resolve(profile="staging", config_root=config_root)
        assert bundle.meta.profile == "staging"
        assert bundle.config["app"]["mode"] == "staging"

    def test_runtime_overrides(self, tmp_path: Path):
        """Runtime overrides merge last and take precedence."""
        config_root = _create_config_tree(
            tmp_path,
            registry='profile_default = "default"\nmodules = []\n',
            **{
                "profiles/default.toml": "[app]\nname = 'original'\n",
            },
        )

        bundle = resolve(
            config_root=config_root,
            overrides={"app": {"name": "overridden"}},
        )
        assert bundle.config["app"]["name"] == "overridden"


class TestResolverErrors:
    def test_missing_config_root_env(self):
        env = {k: v for k, v in os.environ.items() if k != "CONFIDANTIC_ROOT"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ConfigRootNotFoundError):
                resolve()

    def test_missing_registry(self, tmp_path: Path):
        config_root = tmp_path / ".devman" / ".config"
        config_root.mkdir(parents=True)
        with pytest.raises(RegistryNotFoundError):
            resolve(config_root=config_root)

    def test_missing_nondefault_profile(self, tmp_path: Path):
        config_root = _create_config_tree(
            tmp_path,
            registry='profile_default = "production"\nmodules = []\n',
        )
        with pytest.raises(ProfileNotFoundError, match="production"):
            resolve(config_root=config_root)

    def test_missing_module(self, tmp_path: Path):
        config_root = _create_config_tree(
            tmp_path,
            registry='profile_default = "default"\nmodules = ["nonexistent"]\n',
        )
        with pytest.raises(ModuleNotFoundError_, match="nonexistent"):
            resolve(config_root=config_root)


class TestSnapshotDeterminism:
    def test_repeated_resolution_same_fingerprint(self, tmp_path: Path):
        """Fingerprint is identical across repeated resolutions."""
        config_root = _create_config_tree(
            tmp_path,
            registry='profile_default = "default"\nmodules = ["app"]\n',
            **{
                "modules/app.toml": textwrap.dedent("""\
                    [service]
                    name = "api"
                    port = 8080
                    tags = ["web", "rest"]
                """),
            },
        )

        b1 = resolve(config_root=config_root)
        b2 = resolve(config_root=config_root)

        # Fingerprints should match (ignoring the timestamp in meta)
        fp1 = snapshot_fingerprint(b1)
        fp2 = snapshot_fingerprint(b2)
        assert fp1 == fp2

    def test_snapshot_json_is_stable(self, tmp_path: Path):
        """JSON snapshot output is identical across runs."""
        config_root = _create_config_tree(
            tmp_path,
            registry='profile_default = "default"\nmodules = []\n',
            **{
                "profiles/default.toml": "[db]\nhost = 'localhost'\nport = 5432\n",
            },
        )

        b1 = resolve(config_root=config_root)
        b2 = resolve(config_root=config_root)

        # Compare snapshots excluding meta.resolved_at and meta.fingerprint
        s1 = json.loads(build_snapshot(b1))
        s2 = json.loads(build_snapshot(b2))
        # Config and datasets should be identical
        assert s1["config"] == s2["config"]
        assert s1["datasets"] == s2["datasets"]


class TestResolverWithDatasets:
    def test_dataset_loading(self, tmp_path: Path):
        """Datasets are loaded and included in the bundle."""
        config_root = _create_config_tree(
            tmp_path,
            registry=textwrap.dedent("""\
                profile_default = "default"
                modules = []

                [datasets.users]
                path = "data/users.jsonl"
                record_model = "tests.fixtures.sample_record.UserRecord"
            """),
            **{
                "data/users.jsonl": (
                    '{"name": "Alice", "email": "alice@example.com"}\n'
                    '{"name": "Bob", "email": "bob@example.com", "role": "admin"}\n'
                ),
            },
        )

        bundle = resolve(config_root=config_root)
        assert "users" in bundle.datasets
        assert len(bundle.datasets["users"]) == 2
        assert bundle.datasets["users"][0]["name"] == "Alice"
        assert bundle.datasets["users"][1]["role"] == "admin"
