"""Stable snapshot contract — deterministic JSON serialization.

Produces output suitable for:
- cue vet input
- Snapshot/golden tests
- Predictable fingerprints

Guarantees:
- Deterministic key ordering
- JSON-safe normalization
- No volatile runtime fields unless intentionally included
"""

from __future__ import annotations

import json
from typing import Any

from confidantic.core.fingerprint import compute_fingerprint
from confidantic.models.resolved import ResolvedBundle


def build_snapshot(bundle: ResolvedBundle, *, redact: bool = True) -> str:
    """Build a stable JSON snapshot string from a ResolvedBundle.

    Args:
        bundle: The resolved bundle to serialize.
        redact: If True (default), mask secrets in the output.

    Returns:
        Deterministic JSON string with sorted keys and 2-space indent.
    """
    data = bundle.to_redacted_dict() if redact else bundle.model_dump()
    normalized = _normalize(data)
    return json.dumps(normalized, sort_keys=True, indent=2, default=str)


def snapshot_fingerprint(bundle: ResolvedBundle) -> str:
    """Compute the fingerprint of a bundle's redacted snapshot.

    Always uses the redacted view for fingerprinting to ensure
    secrets don't influence the hash. Excludes volatile fields
    (resolved_at, fingerprint) to ensure stability across runs.
    """
    data = bundle.to_redacted_dict()
    # Strip volatile meta fields that change per-run
    if "meta" in data:
        data["meta"] = {
            k: v
            for k, v in data["meta"].items()
            if k not in ("resolved_at", "fingerprint")
        }
    normalized = _normalize(data)
    return compute_fingerprint(normalized)


def _normalize(value: Any) -> Any:
    """Recursively normalize a value for deterministic JSON output.

    - Sorts dict keys
    - Converts non-JSON-safe types to strings
    - Preserves list order (lists are semantically ordered)
    """
    if isinstance(value, dict):
        return {k: _normalize(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    # Convert anything else to string
    return str(value)
