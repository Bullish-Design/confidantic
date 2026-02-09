"""CUE exporter — discovers export target models and writes CUE files.

Workflow:
1. Discover export target models (from registry or explicit list)
2. Transform Pydantic model schema to CUE definitions
3. Write files into build/schemas/cue/
4. Run cue fmt on generated outputs
"""

from __future__ import annotations

import importlib
import logging
import subprocess
from pathlib import Path

from pydantic import BaseModel

from confidantic.core.errors import CueError
from confidantic.cue_export.emitters import emit_cue_definition
from confidantic.cue_export.naming import model_to_cue_filename

logger = logging.getLogger("confidantic.cue_export")


def export_models(
    model_paths: list[str],
    *,
    output_dir: Path,
    package_name: str = "confidantic",
    run_fmt: bool = True,
) -> list[Path]:
    """Export Pydantic models to CUE schema files.

    Args:
        model_paths: Dotted import paths to Pydantic model classes.
        output_dir: Directory to write CUE files into.
        package_name: CUE package name for the generated files.
        run_fmt: If True, run `cue fmt` on each generated file.

    Returns:
        List of paths to generated CUE files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    for dotted_path in model_paths:
        model_cls = _import_model(dotted_path)
        cue_content = emit_cue_definition(model_cls, package_name=package_name)
        filename = model_to_cue_filename(model_cls.__name__)
        out_path = output_dir / filename

        out_path.write_text(cue_content, encoding="utf-8")
        logger.info("Exported %s -> %s", dotted_path, out_path)
        generated.append(out_path)

    if run_fmt and generated:
        cue_fmt(generated)

    return generated


def cue_fmt(paths: list[Path]) -> None:
    """Run `cue fmt` on a list of CUE files."""
    for path in paths:
        logger.debug("Running cue fmt on %s", path)
        result = subprocess.run(
            ["cue", "fmt", str(path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise CueError("fmt", result.stderr.strip(), result.returncode)


def _import_model(dotted_path: str) -> type[BaseModel]:
    """Import a Pydantic model class from a dotted path."""
    module_path, _, class_name = dotted_path.rpartition(".")
    if not module_path:
        raise ValueError(f"Invalid model path (no module): {dotted_path}")

    module = importlib.import_module(module_path)
    cls = getattr(module, class_name, None)
    if cls is None:
        raise ValueError(f"'{module_path}' has no attribute '{class_name}'")
    if not isinstance(cls, type) or not issubclass(cls, BaseModel):
        raise ValueError(f"'{dotted_path}' is not a Pydantic BaseModel subclass")

    return cls
