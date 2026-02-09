"""Tests for profile resolution precedence."""

import os
from unittest.mock import patch

from confidantic.core.resolver import _resolve_profile


class TestProfilePrecedence:
    def test_explicit_arg_wins(self):
        """Explicit API arg is highest precedence."""
        with patch.dict(os.environ, {"CONFIDANTIC_PROFILE": "env_profile"}):
            result = _resolve_profile("explicit", "registry_default")
        assert result == "explicit"

    def test_env_var_second(self):
        """CONFIDANTIC_PROFILE env var when no explicit arg."""
        with patch.dict(os.environ, {"CONFIDANTIC_PROFILE": "env_profile"}):
            result = _resolve_profile(None, "registry_default")
        assert result == "env_profile"

    def test_registry_default_third(self):
        """Registry profile_default when no explicit arg or env var."""
        with patch.dict(os.environ, {}, clear=True):
            env = os.environ.copy()
            env.pop("CONFIDANTIC_PROFILE", None)

        with patch.dict(os.environ, env, clear=True):
            result = _resolve_profile(None, "registry_default")
        assert result == "registry_default"

    def test_fallback_to_default(self):
        """Fallback to "default" when nothing else is set."""
        with patch.dict(os.environ, {}, clear=True):
            env = os.environ.copy()
            env.pop("CONFIDANTIC_PROFILE", None)

        with patch.dict(os.environ, env, clear=True):
            result = _resolve_profile(None, "")
        assert result == "default"

    def test_none_explicit_with_empty_env(self):
        """None explicit + empty env + valid registry default."""
        env = {k: v for k, v in os.environ.items() if k != "CONFIDANTIC_PROFILE"}
        with patch.dict(os.environ, env, clear=True):
            result = _resolve_profile(None, "ci")
        assert result == "ci"
