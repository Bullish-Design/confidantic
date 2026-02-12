"""Strict wrapper helpers for invoking the ``cue`` binary deterministically."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


def check_cue_available() -> bool:
    """Return ``True`` when the ``cue`` executable is available on ``PATH``."""
    return shutil.which("cue") is not None


def _run_cue_command(
    args: list[str],
    *,
    context: str,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
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
        cwd=str(cwd) if cwd is not None else None,
    )

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        cwd_line = f"cwd: {cwd}\n" if cwd is not None else ""
        raise subprocess.CalledProcessError(
            returncode=result.returncode,
            cmd=result.args,
            output=result.stdout,
            stderr=(
                f"{context} failed with exit code {result.returncode}.\n"
                f"{cwd_line}"
                f"stdout:\n{stdout or '(empty)'}\n"
                f"stderr:\n{stderr or '(empty)'}"
            ),
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


def run_cue_vet(
    path: Path,
    schema: Path | None = None,
    *,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
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

    run_cwd = Path(cwd) if cwd is not None else None
    if run_cwd is not None and not run_cwd.exists():
        raise FileNotFoundError(
            f"Cannot run cue vet: working directory does not exist: {run_cwd}"
        )

    return _run_cue_command(
        args,
        context=f"cue vet for {target}",
        cwd=run_cwd,
    )
