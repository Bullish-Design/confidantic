"""Structured error types for Confidantic."""

from __future__ import annotations

from pathlib import Path


class ConfidanticError(Exception):
    """Base exception for all Confidantic errors."""


class ConfigRootNotFoundError(ConfidanticError):
    """CONFIDANTIC_ROOT is not set or the directory does not exist."""

    def __init__(self, path: Path | None = None) -> None:
        if path is None:
            msg = (
                "CONFIDANTIC_ROOT is not set. "
                "Ensure the confidantic devenv module is imported."
            )
        else:
            msg = f"CONFIDANTIC_ROOT directory does not exist: {path}"
        super().__init__(msg)
        self.path = path


class RegistryNotFoundError(ConfidanticError):
    """confidantic.toml not found in CONFIDANTIC_ROOT."""

    def __init__(self, root: Path) -> None:
        super().__init__(f"confidantic.toml not found in {root}")
        self.root = root


class ProfileNotFoundError(ConfidanticError):
    """Requested profile TOML file does not exist."""

    def __init__(self, profile: str, path: Path) -> None:
        super().__init__(f"Profile '{profile}' not found: {path}")
        self.profile = profile
        self.path = path


class ModuleNotFoundError_(ConfidanticError):
    """Declared module TOML file does not exist."""

    def __init__(self, module: str, path: Path) -> None:
        super().__init__(f"Module '{module}' not found: {path}")
        self.module = module
        self.path = path


class TomlLoadError(ConfidanticError):
    """Error loading or validating a TOML file."""

    def __init__(self, path: Path, key_path: str, detail: str) -> None:
        super().__init__(f"{path} [{key_path}]: {detail}")
        self.path = path
        self.key_path = key_path
        self.detail = detail


class JsonlParseWarning:
    """Warning for an invalid JSONL line (not raised, collected)."""

    def __init__(self, path: Path, line_number: int, detail: str) -> None:
        self.path = path
        self.line_number = line_number
        self.detail = detail

    def __str__(self) -> str:
        return f"{self.path}:{self.line_number}: {self.detail}"

    def __repr__(self) -> str:
        return f"JsonlParseWarning({self.path}:{self.line_number})"


class JsonlValidationError(ConfidanticError):
    """Raised when strict JSONL mode is active and invalid lines exist."""

    def __init__(self, path: Path, warnings: list[JsonlParseWarning]) -> None:
        lines = ", ".join(str(w.line_number) for w in warnings)
        super().__init__(f"{path}: invalid lines at {lines}")
        self.path = path
        self.warnings = warnings


class DatasetNotFoundError(ConfidanticError):
    """Declared dataset file does not exist."""

    def __init__(self, name: str, path: Path) -> None:
        super().__init__(f"Dataset '{name}' not found: {path}")
        self.name = name
        self.path = path


class CueError(ConfidanticError):
    """Error running a CUE command."""

    def __init__(self, command: str, stderr: str, returncode: int) -> None:
        super().__init__(f"cue {command} failed (exit {returncode}): {stderr}")
        self.command = command
        self.stderr = stderr
        self.returncode = returncode
