"""Tests for redaction defaults in workshop objects."""

from __future__ import annotations

from pathlib import Path

from confidantic.workshop.loaders import load_workshop_input
from confidantic.workshop.models import to_redacted_dict


def test_workshop_input_redacts_sensitive_paths() -> None:
    workshop_input = load_workshop_input(
        grammar_name="python",
        node_types_path=Path("tests/fixtures/python/node-types.json"),
        queries_dir=Path("tests/fixtures/python/queries"),
    )
    redacted = to_redacted_dict(workshop_input)
    serialized = str(redacted)

    assert "tests/fixtures/python/node-types.json" not in serialized
    assert "[REDACTED]" in serialized


def test_nested_redaction_masks_common_secret_keys() -> None:
    payload = {
        "api_key": "abc123",
        "nested": {"token": "xyz", "ok": "value"},
    }
    redacted = to_redacted_dict(payload)
    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["nested"]["token"] == "[REDACTED]"
    assert redacted["nested"]["ok"] == "value"
