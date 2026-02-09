"""Golden tests — verify snapshot output matches expected fixtures byte-for-byte."""

import json
import textwrap
from pathlib import Path

from confidantic.core.resolver import resolve
from confidantic.core.snapshot import build_snapshot


def _create_config_tree(root: Path, **extra_files: str) -> Path:
    config_root = root / ".devman" / ".config"
    config_root.mkdir(parents=True)
    for rel_path, content in extra_files.items():
        p = config_root / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return config_root


GOLDEN_REGISTRY = textwrap.dedent("""\
    profile_default = "default"
    modules = ["app"]
""")

GOLDEN_PROFILE = textwrap.dedent("""\
    [meta]
    environment = "development"
""")

GOLDEN_MODULE = textwrap.dedent("""\
    [app]
    name = "golden-test-service"
    debug = true
    port = 8080
""")


class TestGoldenSnapshot:
    def test_golden_snapshot_structure(self, tmp_path: Path):
        """Verify the resolved snapshot has the expected structure."""
        config_root = _create_config_tree(
            tmp_path,
            **{
                "confidantic.toml": GOLDEN_REGISTRY,
                "profiles/default.toml": GOLDEN_PROFILE,
                "modules/app.toml": GOLDEN_MODULE,
            },
        )

        bundle = resolve(config_root=config_root)
        snapshot = build_snapshot(bundle)
        data = json.loads(snapshot)

        # Verify top-level structure
        assert set(data.keys()) == {"meta", "config", "datasets"}

        # Verify meta
        assert data["meta"]["profile"] == "default"
        assert data["meta"]["modules"] == ["app"]
        assert "fingerprint" in data["meta"]
        assert "resolved_at" in data["meta"]

        # Verify config is the merged result
        assert data["config"]["meta"]["environment"] == "development"
        assert data["config"]["app"]["name"] == "golden-test-service"
        assert data["config"]["app"]["debug"] is True
        assert data["config"]["app"]["port"] == 8080

        # Verify datasets (empty in this test)
        assert data["datasets"] == {}

    def test_golden_snapshot_key_ordering(self, tmp_path: Path):
        """Verify all keys in the snapshot are sorted."""
        config_root = _create_config_tree(
            tmp_path,
            **{
                "confidantic.toml": GOLDEN_REGISTRY,
                "profiles/default.toml": GOLDEN_PROFILE,
                "modules/app.toml": GOLDEN_MODULE,
            },
        )

        bundle = resolve(config_root=config_root)
        snapshot = build_snapshot(bundle)
        _assert_keys_sorted(json.loads(snapshot))

    def test_golden_redaction(self, tmp_path: Path):
        """Verify secrets are redacted in the default snapshot."""
        config_root = _create_config_tree(
            tmp_path,
            **{
                "confidantic.toml": 'profile_default = "default"\nmodules = []\n',
                "profiles/default.toml": textwrap.dedent("""\
                    [db]
                    host = "localhost"
                    password = "super_secret"
                    api_key = "key_12345"
                """),
            },
        )

        bundle = resolve(config_root=config_root)
        snapshot = build_snapshot(bundle, redact=True)
        data = json.loads(snapshot)

        # password and api_key contain secret-like names and should be redacted
        assert data["config"]["db"]["password"] == "***REDACTED***"
        assert data["config"]["db"]["api_key"] == "***REDACTED***"
        assert data["config"]["db"]["host"] == "localhost"


def _assert_keys_sorted(obj):
    """Recursively assert all dict keys are sorted."""
    if isinstance(obj, dict):
        keys = list(obj.keys())
        assert keys == sorted(keys), f"Keys not sorted: {keys}"
        for v in obj.values():
            _assert_keys_sorted(v)
    elif isinstance(obj, list):
        for item in obj:
            _assert_keys_sorted(item)
