"""Deterministic TOML loader with Pydantic validation at parse boundary."""

from __future__ import annotations

import logging
import tomllib
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from confidantic.core.errors import TomlLoadError

logger = logging.getLogger("confidantic.loader_toml")

T = TypeVar("T", bound=BaseModel)


def load_toml_raw(path: Path) -> dict[str, Any]:
    """Load a TOML file and return the raw dict.

    Raises TomlLoadError with file path and detail on parse failure.
    """
    if not path.exists():
        raise TomlLoadError(path, "<root>", "file does not exist")
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise TomlLoadError(path, "<root>", f"TOML parse error: {exc}") from exc


def load_toml_validated(path: Path, model_cls: type[T]) -> T:
    """Load a TOML file and validate it against a Pydantic model.

    Returns an instance of model_cls. Raises TomlLoadError with
    user-readable messages including file path, key path, and
    expected/actual type details.
    """
    raw = load_toml_raw(path)
    return validate_toml_data(raw, path, model_cls)


def validate_toml_data(
    data: dict[str, Any], source_path: Path, model_cls: type[T]
) -> T:
    """Validate a raw TOML dict against a Pydantic model."""
    try:
        return model_cls.model_validate(data)
    except ValidationError as exc:
        errors = exc.errors()
        if errors:
            first = errors[0]
            key_path = " -> ".join(str(loc) for loc in first.get("loc", []))
            detail = first.get("msg", str(exc))
            expected = first.get("type", "unknown")
            raise TomlLoadError(
                source_path,
                key_path or "<root>",
                f"{detail} (type: {expected})",
            ) from exc
        raise TomlLoadError(
            source_path, "<root>", f"validation failed: {exc}"
        ) from exc


def load_toml_as_dict(path: Path) -> dict[str, Any]:
    """Load a TOML file as a plain dict for merge operations.

    Does not validate against a Pydantic model — used for loading
    profile overlays and module configs before merging.
    """
    logger.debug("Loading TOML: %s", path)
    return load_toml_raw(path)
