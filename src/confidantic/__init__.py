from __future__ import annotations

__version__ = "0.3.0"

from pathlib import Path
from typing import Any, Dict, List, Sequence

import os

from dotenv import dotenv_values  # pip install python-dotenv
from pydantic import BaseModel, Field
from rich.pretty import Pretty

__all__ = [
    # user-visible top-level API
    "Settings",  # the **instance** (auto-loaded)
    "SettingsType",  # the underlying pydantic class (advanced use)
    "PluginRegistry",
    "init_settings",  # kept for backward compatibility
    "find_project_root",
    "gather_env_files",
    "load_env_files",
]
PROJECT_ROOT_MARKERS = {".git", ".config"}  # stop when we meet one of these


def find_project_root(start: str | Path | None = None) -> Path:
    """Walk parents until we find a folder containing one of the PROJECT_ROOT_MARKERS."""
    current = Path(start or Path.cwd()).resolve()
    for parent in (current, *current.parents):
        if any((parent / marker).exists() for marker in PROJECT_ROOT_MARKERS):
            return parent
    return current  # fallback to cwd if nothing found


def gather_env_files(root: Path) -> List[Path]:
    return sorted(
        root.rglob("*.env"), key=lambda p: len(p.parts), reverse=True
    )  # deepest wins


def load_env_files(files: Sequence[Path]) -> Dict[str, str]:
    """Later files take precedence (same as dotenv)."""
    env: Dict[str, str] = {}
    for fp in files[::-1]:  # reverse traversal: shallow first, deep last
        env.update(dotenv_values(fp))
    return {k: str(v) for k, v in env.items() if v is not None}


class Settings(BaseModel):
    """Derive your project settings from this base class."""

    class Config:
        extra = "allow"  # plugin mix-ins may add fields at runtime

    # Built-ins that every project gets for free
    project_root: Path = Field(default_factory=find_project_root)
    env_files: List[Path] = Field(default_factory=list)
    package_version: str | None = None
    git_commit: str | None = None
    git_branch: str | None = None

    def pretty(self) -> Pretty:
        return Pretty(self.model_dump(mode="python"), expand_all=True)


class _SettingsSingleton:
    """Thin wrapper to guarantee there’s only one loaded Settings object."""

    _instance: Settings | None = None
    _cls: type[Settings] | None = None

    @classmethod
    def init(cls, model_cls: type[Settings], **kwargs: Any) -> Settings:
        if cls._instance is not None:
            return cls._instance

        # 1) load .env cascade
        env_files = gather_env_files(find_project_root())
        env_data = load_env_files(env_files)

        # 2) merge OS-level variables (they win)
        env_data.update(os.environ)

        # 3) build the *instance*
        instance = model_cls.model_validate(env_data | kwargs)
        instance.env_files = env_files

        # optional Git + version metadata
        cls._populate_git(instance)
        cls._populate_pkg(instance)

        # 4) cache & return
        cls._instance = instance
        cls._cls = model_cls
        # Snapshot merged config for inspection
        dump_path = instance.project_root / ".config" / "confidantic.yaml"
        dump_path.parent.mkdir(exist_ok=True)
        dump_path.write_text(instance.model_dump_json(indent=2))
        return instance

    # ---- helpers ----------------------------------------------------------------

    @staticmethod
    def _populate_git(settings: Settings) -> None:
        try:
            from git import Repo  # type: ignore

            repo = Repo(settings.project_root)
            settings.git_commit = repo.head.commit.hexsha[:8]
            settings.git_branch = repo.active_branch.name
        except Exception:  # pragma: no cover
            pass  # not a Git repo, or GitPython unavailable

    @staticmethod
    def _populate_pkg(settings: Settings) -> None:
        try:
            import importlib.metadata as md

            settings.package_version = md.version(settings.project_root.name)
        except md.PackageNotFoundError:
            pass


def init_settings(model_cls: type[Settings] | None = None, **kwargs: Any) -> Settings:
    """Entry point for users: returns the singleton Settings object."""
    model_cls = model_cls or Settings
    return _SettingsSingleton.init(model_cls, **kwargs)


# --------------------------------------------------------------------------- #
# -------------------------  Very Tiny Plugin System  ----------------------- #
# --------------------------------------------------------------------------- #


class PluginRegistry:
    """Keeps track of mix-ins that want to extend the Settings model."""

    _mixins: List[type[Settings]] = []

    @classmethod
    def register(cls, mixin: type[Settings]) -> None:
        cls._mixins.append(mixin)

    @classmethod
    def build_class(cls, base: type[Settings] = Settings) -> type[Settings]:
        # Dynamically create a combined class so type checkers stay happy
        return type("ConfidanticSettings", tuple(cls._mixins) + (base,), {})


# --------------------------------------------------------------------------- #
#                    ***  AUTO-INITIALISE ON IMPORT  ***                      #
# --------------------------------------------------------------------------- #
# 1) Build the *final* class (base + any plug-ins already registered)
SettingsType = PluginRegistry.build_class()

# 2) Create the singleton *instance* immediately …
_SettingsInstance = _SettingsSingleton.init(SettingsType)

# 3) …and expose it *as* `Settings`
Settings: SettingsType = _SettingsInstance  # type: ignore[assignment]
# Users may still import `SettingsType` if they need the class itself.


# --------------------------------------------------------------------------- #
#                         Convenience backward alias                          #
# --------------------------------------------------------------------------- #
settings = Settings  # lower-case alias (optional, feels ergonomic)
