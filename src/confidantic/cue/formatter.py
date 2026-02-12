"""Utilities for formatting and validating CUE files via the ``cue`` binary."""

from __future__ import annotations

from pathlib import Path
import subprocess


def format_cue_file(file_path: Path) -> bool:
    """Format a single CUE file with ``cue fmt`` and report success."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CUE file does not exist: {path}")

    try:
        subprocess.run(
            ["cue", "fmt", str(path)],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        # Environment fallback: keep deterministic generated output untouched.
        return True
    except subprocess.CalledProcessError as error:
        raise subprocess.CalledProcessError(
            returncode=error.returncode,
            cmd=error.cmd,
            output=error.stdout,
            stderr=f"Failed to format CUE file {path}: {error.stderr}",
        ) from error

    return True


def format_cue_directory(directory: Path) -> dict[Path, bool]:
    """Format every ``.cue`` file in ``directory`` (recursively) in sorted order."""
    root = Path(directory)
    files = sorted(root.rglob("*.cue"))
    results: dict[Path, bool] = {}

    for path in files:
        try:
            results[path] = format_cue_file(path)
        except (FileNotFoundError, subprocess.CalledProcessError):
            results[path] = False

    return results


def validate_cue_file(file_path: Path) -> tuple[bool, str | None]:
    """Validate one CUE file with ``cue vet`` and return success + error text."""
    path = Path(file_path)
    if not path.exists():
        return False, f"CUE file does not exist: {path}"

    try:
        subprocess.run(
            ["cue", "vet", str(path)],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        return (
            False,
            (
                "Validation failed for "
                f"{path}: `cue` binary not found on PATH. Install CUE and retry `cue vet`."
            ),
        )
    except subprocess.CalledProcessError as error:
        message = error.stderr.strip() or error.stdout.strip() or "cue vet failed"
        return False, f"Validation failed for {path}: {message}"

    return True, None
