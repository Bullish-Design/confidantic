#!/usr/bin/env python3
"""Phase 6 quality-gate runner (CI/CD equivalent without GitHub Actions)."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run(cmd: list[str], env: dict[str, str]) -> int:
    print("+", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=REPO_ROOT, env=env)
    return completed.returncode


def _ensure_confidantic_root(env: dict[str, str]) -> None:
    root = env.get("CONFIDANTIC_ROOT") or str(REPO_ROOT / ".devman" / ".config")
    Path(root).mkdir(parents=True, exist_ok=True)
    env["CONFIDANTIC_ROOT"] = root


def run_suite(name: str, env: dict[str, str]) -> int:
    suites: dict[str, list[list[str]]] = {
        "test": [["pytest", "tests/", "-v", "--cov=src/confidantic", "--cov-report=term"]],
        "quality": [
            ["pytest", "tests/integration/test_golden_snapshots.py", "-v"],
            ["pytest", "tests/integration/test_cue_formatting.py", "-v"],
            ["pytest", "tests/integration/test_jsonl_behavior.py", "-v"],
            ["pytest", "tests/integration/test_redaction.py", "-v"],
        ],
        "performance": [["pytest", "tests/performance/", "-v"]],
        "e2e": [["pytest", "tests/integration/workshop/", "-v"]],
    }
    for command in suites[name]:
        code = _run(command, env)
        if code != 0:
            return code
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "suite",
        choices=["test", "quality", "performance", "e2e", "all"],
        default="all",
        nargs="?",
        help="Suite to run (default: all)",
    )
    args = parser.parse_args()

    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + (os.pathsep + existing_pythonpath if existing_pythonpath else "")
    _ensure_confidantic_root(env)

    ordered = ["test", "quality", "performance", "e2e"] if args.suite == "all" else [args.suite]
    for suite in ordered:
        print(f"\n== Running {suite} suite ==")
        code = run_suite(suite, env)
        if code != 0:
            print(f"Suite failed: {suite}")
            return code

    print("All requested phase-6 quality gates passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
