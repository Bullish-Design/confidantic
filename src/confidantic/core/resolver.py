"""Resolver pipeline — orchestrates the full configuration resolution.

Resolution order:
1. Resolve profile precedence (explicit arg > env > registry default > "default")
2. Load registry (confidantic.toml)
3. Load profile overlay (profiles/<profile>.toml)
4. Load modules in deterministic declared order
5. Load datasets
6. Apply explicit runtime overrides/context
7. Build ResolvedBundle
8. Compute fingerprint from normalized redacted snapshot
"""

from __future__ import annotations

import importlib
import logging
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from confidantic.core.context import load_context
from confidantic.core.errors import (
    ConfigRootNotFoundError,
    DatasetNotFoundError,
    ModuleNotFoundError_,
    ProfileNotFoundError,
    RegistryNotFoundError,
)
from confidantic.core.fingerprint import compute_fingerprint
from confidantic.core.loader_jsonl import load_jsonl
from confidantic.core.loader_toml import load_toml_as_dict, load_toml_validated
from confidantic.core.merge import deep_merge
from confidantic.models.metadata import DevmanContext
from confidantic.models.registry import RegistryConfig
from confidantic.models.resolved import ResolvedBundle, ResolutionMeta

logger = logging.getLogger("confidantic.resolver")


def resolve(
    *,
    profile: str | None = None,
    config_root: Path | None = None,
    overrides: dict[str, Any] | None = None,
    context: DevmanContext | None = None,
) -> ResolvedBundle:
    """Run the full configuration resolution pipeline.

    Args:
        profile: Explicit profile name (highest precedence).
        config_root: Explicit CONFIDANTIC_ROOT path. If None, read from env.
        overrides: Runtime overrides to merge last.
        context: Optional DevmanContext. If None, auto-detected.

    Returns:
        A fully resolved ResolvedBundle.
    """
    # Step 0: Resolve config root
    root = _resolve_config_root(config_root)
    logger.debug("Config root: %s", root)

    # Step 1: Load registry
    registry_path = root / "confidantic.toml"
    if not registry_path.exists():
        raise RegistryNotFoundError(root)
    registry = load_toml_validated(registry_path, RegistryConfig)
    logger.debug("Registry loaded: profile_default=%s, modules=%s",
                 registry.profile_default, registry.modules)

    # Step 2: Resolve profile name
    resolved_profile = _resolve_profile(profile, registry.profile_default)
    logger.debug("Resolved profile: %s", resolved_profile)

    # Step 3: Start with empty config, merge profile overlay
    config: dict[str, Any] = {}

    profile_path = root / "profiles" / f"{resolved_profile}.toml"
    if profile_path.exists():
        profile_data = load_toml_as_dict(profile_path)
        config = deep_merge(config, profile_data)
        logger.debug("Merged profile overlay: %s", resolved_profile)
    elif resolved_profile != "default":
        # Non-default profile must exist
        raise ProfileNotFoundError(resolved_profile, profile_path)
    # else: default profile is optional

    # Step 4: Load and merge modules in declared order
    for module_name in registry.modules:
        module_path = root / "modules" / f"{module_name}.toml"
        if not module_path.exists():
            raise ModuleNotFoundError_(module_name, module_path)
        module_data = load_toml_as_dict(module_path)
        config = deep_merge(config, module_data)
        logger.debug("Merged module: %s", module_name)

    # Step 5: Load datasets
    datasets: dict[str, list[dict[str, Any]]] = {}
    for ds_name, ds_decl in registry.datasets.items():
        ds_path = root / ds_decl.path
        if not ds_path.exists():
            raise DatasetNotFoundError(ds_name, ds_path)

        model_cls = _import_model(ds_decl.record_model)
        result = load_jsonl(ds_path, model_cls, strict=registry.strict_jsonl)
        datasets[ds_name] = result.record_dicts

        if result.warnings:
            for w in result.warnings:
                logger.warning("Dataset %s: %s", ds_name, w)

    # Step 6: Apply runtime overrides
    if overrides:
        config = deep_merge(config, overrides)
        logger.debug("Applied runtime overrides")

    # Step 7: Apply context as metadata
    if context is None:
        context = load_context(config_root=root)

    # Step 8: Build the bundle
    meta = ResolutionMeta(
        profile=resolved_profile,
        modules=list(registry.modules),
        fingerprint="",  # computed below
    )

    bundle = ResolvedBundle(
        meta=meta,
        config=config,
        datasets=datasets,
    )

    # Step 9: Compute fingerprint from redacted snapshot
    redacted = bundle.to_redacted_dict()
    fingerprint = compute_fingerprint(redacted)
    bundle.meta.fingerprint = fingerprint
    logger.debug("Fingerprint: %s", fingerprint)

    return bundle


def _resolve_config_root(explicit: Path | None) -> Path:
    """Determine CONFIDANTIC_ROOT, raising if not found."""
    if explicit is not None:
        if not explicit.is_dir():
            raise ConfigRootNotFoundError(explicit)
        return explicit

    env_val = os.environ.get("CONFIDANTIC_ROOT")
    if not env_val:
        raise ConfigRootNotFoundError(None)

    root = Path(env_val)
    if not root.is_dir():
        raise ConfigRootNotFoundError(root)
    return root


def _resolve_profile(explicit: str | None, registry_default: str) -> str:
    """Resolve profile name by precedence.

    1. Explicit API argument
    2. CONFIDANTIC_PROFILE env var (if set externally)
    3. Registry profile_default
    4. Fallback "default"
    """
    if explicit is not None:
        return explicit

    env_profile = os.environ.get("CONFIDANTIC_PROFILE")
    if env_profile:
        return env_profile

    return registry_default or "default"


def _import_model(dotted_path: str) -> type[BaseModel]:
    """Import a Pydantic model class from a dotted import path.

    E.g. "myapp.models.UserRecord" -> <class UserRecord>.
    """
    module_path, _, class_name = dotted_path.rpartition(".")
    if not module_path:
        raise ValueError(f"Invalid model path (no module): {dotted_path}")

    try:
        module = importlib.import_module(module_path)
    except ImportError as exc:
        raise ValueError(
            f"Could not import module '{module_path}' for model '{dotted_path}'"
        ) from exc

    cls = getattr(module, class_name, None)
    if cls is None:
        raise ValueError(
            f"Module '{module_path}' has no attribute '{class_name}'"
        )

    if not isinstance(cls, type) or not issubclass(cls, BaseModel):
        raise ValueError(
            f"'{dotted_path}' is not a Pydantic BaseModel subclass"
        )

    return cls
