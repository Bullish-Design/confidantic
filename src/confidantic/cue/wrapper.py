"""Python interface for the confidantic-cue wrapper.

Provides programmatic access to CUE validation operations
that the shell wrapper (devenv/bin/confidantic-cue) exposes.
"""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

from confidantic.core.errors import CueError

logger = logging.getLogger("confidantic.cue.wrapper")


def cue_vet(
    data_path: Path,
    schema_paths: list[Path],
    *,
    expression: str | None = None,
) -> None:
    """Run `cue vet` on data against schema(s).

    Args:
        data_path: Path to the JSON data file to validate.
        schema_paths: Paths to CUE schema files.
        expression: Optional CUE expression to scope validation.

    Raises:
        CueError: If validation fails.
    """
    cmd = ["cue", "vet"]
    for sp in schema_paths:
        cmd.append(str(sp))
    cmd.append(str(data_path))

    if expression:
        cmd.extend(["-d", expression])

    logger.debug("Running: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise CueError("vet", result.stderr.strip(), result.returncode)


def cue_vet_jsonl(
    jsonl_path: Path,
    schema_paths: list[Path],
    *,
    expression: str | None = None,
    jq_transform: str | None = None,
) -> list[str]:
    """Validate JSONL records against CUE schema(s).

    Each valid JSON line is extracted and validated individually.
    Returns a list of error messages for lines that fail validation.

    Args:
        jsonl_path: Path to the JSONL file.
        schema_paths: CUE schema file paths.
        expression: Optional CUE expression.
        jq_transform: Optional jq filter to apply to each record before vet.
    """
    errors: list[str] = []

    with open(jsonl_path, encoding="utf-8") as fh:
        for line_num, raw_line in enumerate(fh, start=1):
            stripped = raw_line.strip()
            if not stripped:
                continue

            try:
                record = json.loads(stripped)
            except json.JSONDecodeError:
                errors.append(f"line {line_num}: invalid JSON")
                continue

            # Apply jq transform if specified
            if jq_transform:
                record = _jq_transform(record, jq_transform)
                if record is None:
                    errors.append(f"line {line_num}: jq transform failed")
                    continue

            # Write temp file and validate
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as tmp:
                json.dump(record, tmp, sort_keys=True)
                tmp_path = Path(tmp.name)

            try:
                cue_vet(tmp_path, schema_paths, expression=expression)
            except CueError as exc:
                errors.append(f"line {line_num}: {exc}")
            finally:
                tmp_path.unlink(missing_ok=True)

    return errors


def _jq_transform(data: dict, expression: str) -> dict | None:
    """Apply a jq expression to a JSON object."""
    try:
        result = subprocess.run(
            ["jq", expression],
            input=json.dumps(data),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            logger.warning("jq transform failed: %s", result.stderr)
            return None
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as exc:
        logger.warning("jq transform error: %s", exc)
        return None
