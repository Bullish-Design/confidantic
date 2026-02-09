"""Integration tests for the CLI commands."""

import json
import textwrap
from pathlib import Path

from typer.testing import CliRunner

from confidantic.cli import app

runner = CliRunner()


def _create_config_tree(root: Path, **files: str) -> Path:
    config_root = root / ".devman" / ".config"
    config_root.mkdir(parents=True)
    for rel_path, content in files.items():
        p = config_root / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return config_root


class TestCLIValidate:
    def test_validate_ok(self, tmp_path: Path):
        config_root = _create_config_tree(
            tmp_path,
            **{
                "confidantic.toml": 'profile_default = "default"\nmodules = []\n',
            },
        )
        result = runner.invoke(app, ["validate", "--root", str(config_root)])
        assert result.exit_code == 0
        assert "ok" in result.output

    def test_validate_missing_root(self, tmp_path: Path):
        result = runner.invoke(
            app, ["validate", "--root", str(tmp_path / "nonexistent")]
        )
        assert result.exit_code == 1


class TestCLIDump:
    def test_dump_json(self, tmp_path: Path):
        config_root = _create_config_tree(
            tmp_path,
            **{
                "confidantic.toml": 'profile_default = "default"\nmodules = []\n',
                "profiles/default.toml": "[app]\nname = 'test'\n",
            },
        )
        result = runner.invoke(
            app, ["dump", "--root", str(config_root), "--format", "json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["config"]["app"]["name"] == "test"

    def test_dump_unsupported_format(self, tmp_path: Path):
        config_root = _create_config_tree(
            tmp_path,
            **{"confidantic.toml": 'profile_default = "default"\nmodules = []\n'},
        )
        result = runner.invoke(
            app, ["dump", "--root", str(config_root), "--format", "yaml"]
        )
        assert result.exit_code == 1


class TestCLIEnv:
    def test_env_output(self, tmp_path: Path):
        config_root = _create_config_tree(
            tmp_path,
            **{
                "confidantic.toml": 'profile_default = "default"\nmodules = []\n',
                "profiles/default.toml": "[app]\nname = 'myapp'\nport = 8080\n",
            },
        )
        result = runner.invoke(app, ["env", "--root", str(config_root)])
        assert result.exit_code == 0
        assert "APP_NAME=myapp" in result.output
        assert "APP_PORT=8080" in result.output


class TestCLIFingerprint:
    def test_fingerprint_output(self, tmp_path: Path):
        config_root = _create_config_tree(
            tmp_path,
            **{"confidantic.toml": 'profile_default = "default"\nmodules = []\n'},
        )
        result = runner.invoke(app, ["fingerprint", "--root", str(config_root)])
        assert result.exit_code == 0
        fp = result.output.strip()
        assert len(fp) == 64  # SHA-256 hex

    def test_fingerprint_deterministic(self, tmp_path: Path):
        config_root = _create_config_tree(
            tmp_path,
            **{
                "confidantic.toml": 'profile_default = "default"\nmodules = []\n',
                "profiles/default.toml": "[x]\ny = 1\n",
            },
        )
        r1 = runner.invoke(app, ["fingerprint", "--root", str(config_root)])
        r2 = runner.invoke(app, ["fingerprint", "--root", str(config_root)])
        assert r1.output.strip() == r2.output.strip()
