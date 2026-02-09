"""Redaction engine — masks secrets for safe logging and output.

Handles:
- SecretStr / SecretBytes fields
- Fields marked with json_schema_extra={"redact": True}
- Recursive traversal through nested models, lists, and dicts
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, SecretBytes, SecretStr

from confidantic.models.base import REDACTED_TOKEN


def redact_model(model: BaseModel) -> dict[str, Any]:
    """Redact a Pydantic model instance, returning a safe dict.

    Masks SecretStr, SecretBytes, and fields flagged with redact metadata.
    Recurses through nested models, lists, and dicts.
    """
    raw = model.model_dump()
    return _redact_with_schema(raw, model)


def _redact_with_schema(data: dict[str, Any], model: BaseModel) -> dict[str, Any]:
    """Redact a dict using the model's field metadata."""
    result: dict[str, Any] = {}

    for key in sorted(data.keys()):
        value = data[key]
        field_info = model.__class__.model_fields.get(key)
        model_value = getattr(model, key, None)

        # Check if the field itself should be redacted
        if _should_redact_field(field_info):
            result[key] = REDACTED_TOKEN
            continue

        # Check if the raw model value is a secret type
        if isinstance(model_value, (SecretStr, SecretBytes)):
            result[key] = REDACTED_TOKEN
            continue

        # Recurse into nested models
        if isinstance(model_value, BaseModel) and isinstance(value, dict):
            result[key] = _redact_with_schema(value, model_value)
            continue

        # Recurse into lists
        if isinstance(value, list):
            result[key] = _redact_list(value, model_value)
            continue

        # Recurse into dicts (without schema)
        if isinstance(value, dict):
            result[key] = _redact_dict(value)
            continue

        result[key] = value

    return result


def _redact_list(values: list[Any], model_values: Any) -> list[Any]:
    """Redact items in a list."""
    result: list[Any] = []
    model_list = model_values if isinstance(model_values, list) else []

    for i, item in enumerate(values):
        model_item = model_list[i] if i < len(model_list) else None

        if isinstance(model_item, BaseModel) and isinstance(item, dict):
            result.append(_redact_with_schema(item, model_item))
        elif isinstance(item, dict):
            result.append(_redact_dict(item))
        elif isinstance(item, list):
            result.append(_redact_list(item, model_item))
        elif isinstance(model_item, (SecretStr, SecretBytes)):
            result.append(REDACTED_TOKEN)
        else:
            result.append(item)

    return result


def _redact_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Redact a plain dict (no schema available)."""
    result: dict[str, Any] = {}
    for key in sorted(data.keys()):
        value = data[key]
        if isinstance(value, dict):
            result[key] = _redact_dict(value)
        elif isinstance(value, list):
            result[key] = _redact_list(value, value)
        else:
            result[key] = value
    return result


def _should_redact_field(field_info: Any) -> bool:
    """Check if a Pydantic FieldInfo has the redact flag set."""
    if field_info is None:
        return False
    extra = getattr(field_info, "json_schema_extra", None)
    if isinstance(extra, dict):
        return bool(extra.get("redact", False))
    return False
