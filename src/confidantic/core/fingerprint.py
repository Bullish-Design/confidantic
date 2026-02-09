"""Deterministic fingerprint generation from normalized redacted snapshots."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def compute_fingerprint(data: dict[str, Any]) -> str:
    """Compute a SHA-256 fingerprint of a normalized dict.

    The dict is serialized to JSON with sorted keys and no extra
    whitespace to ensure deterministic output across runs.
    """
    normalized = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
