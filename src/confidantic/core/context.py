"""DevmanContext loading — populates runtime context from environment."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from confidantic.models.metadata import DevmanContext


def load_context(
    *,
    repo_root: Path | None = None,
    config_root: Path | None = None,
) -> DevmanContext:
    """Build a DevmanContext from environment and optional overrides.

    Detects:
    - CONFIDANTIC_ROOT from environment (or override)
    - repo root from CONFIDANTIC_ROOT parent path (or override)
    - jj workspace info (best-effort)
    """
    if config_root is None:
        env_root = os.environ.get("CONFIDANTIC_ROOT")
        if env_root:
            config_root = Path(env_root)

    if repo_root is None and config_root is not None:
        # CONFIDANTIC_ROOT is <repo>/.devman/.config
        # So repo_root is two levels up
        candidate = config_root.parent.parent
        if candidate.exists():
            repo_root = candidate

    jj_rev = _detect_jj_rev(repo_root)
    jj_root = _detect_jj_root(repo_root)

    return DevmanContext(
        repo_root=repo_root,
        config_root=config_root,
        jj_rev=jj_rev,
        jj_root=jj_root,
    )


def _detect_jj_rev(repo_root: Path | None) -> str | None:
    """Best-effort: get current jj working-copy revision."""
    if repo_root is None:
        return None
    try:
        result = subprocess.run(
            ["jj", "log", "-r", "@", "--no-graph", "-T", 'commit_id ++ "\\n"'],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            rev = result.stdout.strip().split("\n")[0].strip()
            return rev if rev else None
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return None


def _detect_jj_root(repo_root: Path | None) -> str | None:
    """Best-effort: get jj workspace root."""
    if repo_root is None:
        return None
    try:
        result = subprocess.run(
            ["jj", "root"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip() or None
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return None
