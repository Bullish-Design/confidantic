"""ResolvedBundle — canonical resolved output of the configuration pipeline."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from confidantic.models.base import REDACTED_TOKEN


class ResolutionMeta(BaseModel):
    """Metadata about how the bundle was resolved."""

    model_config = ConfigDict(extra="forbid")

    profile: str = Field(description="The profile that was resolved.")
    modules: list[str] = Field(
        default_factory=list,
        description="Ordered list of modules that were loaded.",
    )
    fingerprint: str = Field(
        default="",
        description="SHA-256 fingerprint of the normalized redacted snapshot.",
    )
    resolved_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 timestamp of resolution.",
    )


class ResolvedBundle(BaseModel):
    """The canonical resolved output for dump, vet, and golden tests.

    Contains:
    - meta: resolution metadata (profile, module order, fingerprint, timestamp)
    - config: merged configuration as a dict tree
    - datasets: validated record payloads keyed by dataset name
    """

    model_config = ConfigDict(extra="forbid")

    meta: ResolutionMeta
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Resolved, merged configuration tree.",
    )
    datasets: dict[str, list[dict[str, Any]]] = Field(
        default_factory=dict,
        description="Validated dataset records keyed by dataset name.",
    )

    def to_redacted_dict(self) -> dict[str, Any]:
        """Return the bundle with secrets masked in config values."""
        return {
            "meta": self.meta.model_dump(),
            "config": _deep_redact(self.config),
            "datasets": {
                name: [_deep_redact(record) for record in records]
                for name, records in self.datasets.items()
            },
        }

    def to_stable_json(self, *, redact: bool = True) -> str:
        """Produce deterministic JSON output suitable for cue vet and golden tests."""
        data = self.to_redacted_dict() if redact else self.model_dump()
        return json.dumps(data, sort_keys=True, indent=2, default=str)


def _deep_redact(value: Any) -> Any:
    """Recursively mask string values that look like secrets."""
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for k in sorted(value.keys()):
            v = value[k]
            # Redact keys that commonly hold secrets
            if any(
                marker in k.lower()
                for marker in ("secret", "password", "token", "key", "credential")
            ):
                result[k] = REDACTED_TOKEN
            else:
                result[k] = _deep_redact(v)
        return result
    if isinstance(value, list):
        return [_deep_redact(item) for item in value]
    return value
