"""Confidantic V2 — Configuration management for devman-managed projects.

Provides deterministic configuration resolution from .devman/.config,
with Pydantic models as runtime source-of-truth and CUE for schema
validation.
"""

from confidantic.models.base import BaseConfig
from confidantic.models.registry import RegistryConfig
from confidantic.models.resolved import ResolvedBundle
from confidantic.models.metadata import DevmanContext

__all__ = [
    "BaseConfig",
    "RegistryConfig",
    "ResolvedBundle",
    "DevmanContext",
]
