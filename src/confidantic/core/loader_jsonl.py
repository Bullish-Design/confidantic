"""JSONL loader with line-by-line parsing and warn-skip behavior."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from confidantic.core.errors import (
    JsonlParseWarning,
    JsonlValidationError,
)

logger = logging.getLogger("confidantic.loader_jsonl")

T = TypeVar("T", bound=BaseModel)


@dataclass
class JsonlResult:
    """Result of loading a JSONL file.

    Contains both successfully parsed records and any warnings
    for lines that could not be parsed or validated.
    """

    records: list[BaseModel] = field(default_factory=list)
    warnings: list[JsonlParseWarning] = field(default_factory=list)
    source_path: Path = field(default_factory=lambda: Path())

    @property
    def record_dicts(self) -> list[dict]:
        """Return records as plain dicts."""
        return [r.model_dump() for r in self.records]


def load_jsonl(
    path: Path,
    model_cls: type[T],
    *,
    strict: bool = False,
) -> JsonlResult:
    """Load a JSONL file, validating each line against model_cls.

    Each file is bound to one record model type. Invalid JSON lines
    are skipped with warnings (including 1-based line numbers) by default.

    Args:
        path: Path to the JSONL file.
        model_cls: Pydantic model class for each record.
        strict: If True, raise JsonlValidationError when any lines fail.

    Returns:
        JsonlResult with parsed records and any warnings.
    """
    if not path.exists():
        raise FileNotFoundError(f"JSONL file not found: {path}")

    result = JsonlResult(source_path=path)

    with open(path, encoding="utf-8") as fh:
        for line_number, raw_line in enumerate(fh, start=1):
            stripped = raw_line.strip()
            if not stripped:
                continue

            # Step 1: parse as JSON
            try:
                data = json.loads(stripped)
            except json.JSONDecodeError as exc:
                warning = JsonlParseWarning(
                    path=path,
                    line_number=line_number,
                    detail=f"invalid JSON: {exc}",
                )
                result.warnings.append(warning)
                logger.warning("%s", warning)
                continue

            # Step 2: validate against Pydantic model
            try:
                record = model_cls.model_validate(data)
                result.records.append(record)
            except ValidationError as exc:
                first_err = exc.errors()[0] if exc.errors() else {}
                detail = first_err.get("msg", str(exc))
                warning = JsonlParseWarning(
                    path=path,
                    line_number=line_number,
                    detail=f"validation error: {detail}",
                )
                result.warnings.append(warning)
                logger.warning("%s", warning)

    if strict and result.warnings:
        raise JsonlValidationError(path, result.warnings)

    return result
