"""BaseConfig — shared foundation for all Confidantic Pydantic models."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, SecretBytes, SecretStr

REDACTED_TOKEN = "***REDACTED***"


class BaseConfig(BaseModel):
    """Base class for Confidantic configuration models.

    Provides:
    - Strict validation defaults (extra=forbid)
    - to_redacted_dict() for safe logging/output
    - Stable JSON serialization helpers
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_default=True,
        ser_json_bytes="base64",
    )

    def to_redacted_dict(self) -> dict[str, Any]:
        """Return a dict with secrets and redacted fields masked."""
        return _redact_value(self.model_dump(), self)

    def to_stable_json(self, *, redact: bool = True) -> str:
        """Serialize to JSON with deterministic key ordering."""
        data = self.to_redacted_dict() if redact else self.model_dump()
        return json.dumps(data, sort_keys=True, default=str)


def _redact_value(value: Any, model: BaseModel | None = None) -> Any:
    """Recursively redact secrets in a value tree."""
    if isinstance(value, (SecretStr, SecretBytes)):
        return REDACTED_TOKEN

    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, val in sorted(value.items()):
            field_info = None
            if model is not None:
                field_info = model.__class__.model_fields.get(key)

            # Check for redact flag in field metadata
            should_redact = False
            if field_info is not None:
                extra = field_info.json_schema_extra
                if isinstance(extra, dict) and extra.get("redact"):
                    should_redact = True

            if should_redact:
                result[key] = REDACTED_TOKEN
            else:
                # Recurse with child model if available
                child_model = None
                if model is not None:
                    child_val = getattr(model, key, None)
                    if isinstance(child_val, BaseModel):
                        child_model = child_val
                result[key] = _redact_value(val, child_model)
        return result

    if isinstance(value, list):
        return [_redact_value(item) for item in value]

    return value
