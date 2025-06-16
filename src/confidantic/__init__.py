__version__ = "0.2.0"
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Sequence

import os

from dotenv import dotenv_values  # pip install python-dotenv
from pydantic import BaseModel, Field
from rich.pretty import Pretty

__all__ = ["Settings", "init_settings", "load_env_files", "PluginRegistry"]

PROJECT_ROOT_MARKERS = {".git", ".config"}  # stop when we meet one of these


def find_project_root(start: Path | str | None = None) -> Path:
    """Walk parents until we find a folder containing one of the PROJECT_ROOT_MARKERS."""
    current = Path(start or Path.cwd()).resolve()
    # print(f"\nFinding project root starting from: {current}")
    for parent in (current, *current.parents):
        # print(f"    Checking parent: {parent}")
        if any((parent / marker).exists() for marker in PROJECT_ROOT_MARKERS):
            # print(f"    ** Found project root: {parent}")
            return parent
    # print("    No project root found, using current working directory -> {current}")
    return current  # fallback to cwd if nothing found


def gather_env_files(root: Path) -> List[Path]:
    return sorted(
        root.rglob("*.env"), key=lambda p: len(p.parts), reverse=True
    )  # deepest wins


def load_env_files(files: Sequence[Path]) -> Dict[str, str]:
    """Merge .env files: later entries override earlier ones."""
    merged: Dict[str, str] = {}
    for file in reversed(list(files)):  # leaf-first override
        merged.update({k: v for k, v in dotenv_values(file).items() if v is not None})
    return merged


class Settings(BaseModel):
    """Derive your project settings from this base class."""

    class Config:
        extra = "allow"  # plugin mix-ins may add fields at runtime

    # Built-ins that every project gets for free
    project_root: Path = Field(default_factory=find_project_root)
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
        # Environment variables first
        env_files = gather_env_files(find_project_root())
        env_data = load_env_files(env_files)
        # CLI or OS overrides win
        env_data.update(os.environ)
        # Build instance
        instance = model_cls(**{**env_data, **kwargs})
        # Populate package / git metadata
        cls._populate_git(instance)
        cls._populate_version(instance)
        cls._instance, cls._cls = instance, model_cls
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
        except Exception:
            pass  # not a git repo or GitPython not installed

    @staticmethod
    def _populate_version(settings: Settings) -> None:
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
