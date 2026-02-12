"""Confidantic V2 — Configuration management for devman-managed projects.

Provides deterministic configuration resolution from .devman/.config,
with Pydantic models as runtime source-of-truth and CUE for schema
validation.
"""

from . import cue, workshop

__all__ = ["workshop", "cue"]
