from __future__ import annotations

import subprocess
from pathlib import Path
import shutil

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIDANTIC_JUSTFILE = REPO_ROOT / "scripts" / "confidantic.just"

REQUIRED_COMPATIBILITY_RECIPES = (
    "schema:export",
    "schema:vet",
    "data:vet",
    "config:validate",
    "config:dump",
    "config:env",
    "config:fingerprint",
)


def _run_just(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["just", "--justfile", str(CONFIDANTIC_JUSTFILE), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_required_compatibility_recipes_are_defined() -> None:
    if shutil.which("just") is None:
        pytest.skip("just is required for compatibility recipe integration tests")

    if not CONFIDANTIC_JUSTFILE.exists():
        pytest.fail(f"Missing expected justfile: {CONFIDANTIC_JUSTFILE}")

    summary = _run_just("--summary")
    assert summary.returncode == 0, summary.stderr

    defined = set(summary.stdout.split())
    missing = [recipe for recipe in REQUIRED_COMPATIBILITY_RECIPES if recipe not in defined]
    assert not missing, f"Missing required compatibility recipes: {missing}"


@pytest.mark.parametrize("recipe", REQUIRED_COMPATIBILITY_RECIPES)
def test_required_compatibility_recipe_exit_codes(recipe: str) -> None:
    if shutil.which("just") is None:
        pytest.skip("just is required for compatibility recipe integration tests")

    result = _run_just(recipe)
    assert result.returncode == 0, (
        f"Expected recipe '{recipe}' to exit with 0. "
        f"exit={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
    )
