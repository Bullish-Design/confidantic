"""DevmanContext — runtime metadata injected into resolution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DevmanContext(BaseModel):
    """Runtime-only context object for injected metadata.

    Populated from the devman environment: repo path, run metadata,
    optional jj workspace info. Kept explicit and serializable.
    """

    model_config = ConfigDict(extra="ignore")

    repo_root: Path | None = Field(
        default=None,
        description="Absolute path to the project repository root.",
    )
    config_root: Path | None = Field(
        default=None,
        description="CONFIDANTIC_ROOT path (.devman/.config).",
    )
    jj_rev: str | None = Field(
        default=None,
        description="Current jj working-copy revision, if available.",
    )
    jj_root: str | None = Field(
        default=None,
        description="jj workspace root, if available.",
    )
    run_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary key-value metadata from the run environment.",
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict (paths as strings)."""
        data = self.model_dump()
        for key in ("repo_root", "config_root"):
            if data.get(key) is not None:
                data[key] = str(data[key])
        return data
