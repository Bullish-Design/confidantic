"""Tests for fingerprint generation."""

from confidantic.core.fingerprint import compute_fingerprint


class TestFingerprint:
    def test_deterministic_output(self):
        data = {"a": 1, "b": {"c": 2}}
        fp1 = compute_fingerprint(data)
        fp2 = compute_fingerprint(data)
        assert fp1 == fp2

    def test_different_data_different_fingerprint(self):
        fp1 = compute_fingerprint({"a": 1})
        fp2 = compute_fingerprint({"a": 2})
        assert fp1 != fp2

    def test_key_order_does_not_matter(self):
        fp1 = compute_fingerprint({"b": 1, "a": 2})
        fp2 = compute_fingerprint({"a": 2, "b": 1})
        assert fp1 == fp2

    def test_returns_hex_string(self):
        fp = compute_fingerprint({"x": 1})
        assert len(fp) == 64  # SHA-256 hex
        assert all(c in "0123456789abcdef" for c in fp)

    def test_nested_key_order(self):
        fp1 = compute_fingerprint({"a": {"z": 1, "y": 2}})
        fp2 = compute_fingerprint({"a": {"y": 2, "z": 1}})
        assert fp1 == fp2
