"""Tests for stable snapshot generation."""

import json

from confidantic.core.snapshot import build_snapshot, snapshot_fingerprint
from confidantic.models.resolved import ResolvedBundle, ResolutionMeta


def _make_bundle(**config) -> ResolvedBundle:
    return ResolvedBundle(
        meta=ResolutionMeta(
            profile="default",
            modules=["app"],
            fingerprint="placeholder",
        ),
        config=config,
    )


class TestBuildSnapshot:
    def test_produces_valid_json(self):
        bundle = _make_bundle(name="test", count=1)
        snapshot = build_snapshot(bundle)
        data = json.loads(snapshot)
        assert data["config"]["name"] == "test"

    def test_keys_are_sorted(self):
        bundle = _make_bundle(z_key=1, a_key=2, m_key=3)
        snapshot = build_snapshot(bundle)
        data = json.loads(snapshot)
        keys = list(data["config"].keys())
        assert keys == sorted(keys)

    def test_deterministic_across_calls(self):
        bundle = _make_bundle(x=1, y=2)
        s1 = build_snapshot(bundle)
        s2 = build_snapshot(bundle)
        assert s1 == s2

    def test_redaction_enabled_by_default(self):
        bundle = _make_bundle(secret_key="hunter2", name="test")
        snapshot = build_snapshot(bundle, redact=True)
        data = json.loads(snapshot)
        assert data["config"]["secret_key"] == "***REDACTED***"
        assert data["config"]["name"] == "test"

    def test_no_redact_shows_secrets(self):
        bundle = _make_bundle(secret_key="hunter2")
        snapshot = build_snapshot(bundle, redact=False)
        data = json.loads(snapshot)
        assert data["config"]["secret_key"] == "hunter2"


class TestSnapshotFingerprint:
    def test_deterministic(self):
        bundle = _make_bundle(a=1, b=2)
        fp1 = snapshot_fingerprint(bundle)
        fp2 = snapshot_fingerprint(bundle)
        assert fp1 == fp2

    def test_different_config_different_fingerprint(self):
        b1 = _make_bundle(a=1)
        b2 = _make_bundle(a=2)
        assert snapshot_fingerprint(b1) != snapshot_fingerprint(b2)
