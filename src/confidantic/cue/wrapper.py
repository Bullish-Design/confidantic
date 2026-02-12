"""Strict wrapper helpers for invoking the ``cue`` binary deterministically."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


def check_cue_available() -> bool:
    """Return ``True`` when the ``cue`` executable is available on ``PATH``."""
    return shutil.which("cue") is not None


def _run_cue_command(args: list[str], *, context: str) -> subprocess.CompletedProcess[str]:
    """Run a cue command with strict error handling and predictable output capture."""
    if not check_cue_available():
        raise RuntimeError(
            f"Cannot run {context}: cue executable was not found on PATH."
        )

    result = subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        details = stderr or stdout or "cue command failed without output"
        raise subprocess.CalledProcessError(
            returncode=result.returncode,
            cmd=result.args,
            output=result.stdout,
            stderr=f"{context} failed: {details}",
        )

    return result


def run_cue_fmt(file_or_dir: Path, check: bool = False) -> subprocess.CompletedProcess[str]:
    """Run ``cue fmt`` against ``file_or_dir``.

    Args:
        file_or_dir: File or directory to format.
        check: If ``True``, run ``cue fmt --check``.
    """
    target = Path(file_or_dir)
    if not target.exists():
        raise FileNotFoundError(f"Cannot run cue fmt: path does not exist: {target}")

    args = ["cue", "fmt"]
    if check:
        args.append("--check")
    args.append(str(target))
    return _run_cue_command(args, context=f"cue fmt for {target}")


def run_cue_vet(path: Path, schema: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Run ``cue vet`` against ``path`` with optional ``schema``.

    The argument order is deterministic: ``cue vet`` + optional schema + path.
    """
    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(f"Cannot run cue vet: path does not exist: {target}")

    args = ["cue", "vet"]
    if schema is not None:
        schema_path = Path(schema)
        if not schema_path.exists():
            raise FileNotFoundError(
                f"Cannot run cue vet: schema path does not exist: {schema_path}"
            )
        args.append(str(schema_path))

    args.append(str(target))
    return _run_cue_command(args, context=f"cue vet for {target}")
