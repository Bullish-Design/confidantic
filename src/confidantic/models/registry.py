"""RegistryConfig — loaded from confidantic.toml at CONFIDANTIC_ROOT."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DatasetDeclaration(BaseModel):
    """A dataset declaration binding a JSONL file to a record model."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(
        description="Relative path from CONFIDANTIC_ROOT to the JSONL file.",
    )
    record_model: str = Field(
        description=(
            "Dotted import path to the Pydantic model class "
            "for records in this dataset."
        ),
    )


class RegistryConfig(BaseModel):
    """Top-level registry loaded from confidantic.toml.

    Declares profile defaults, activated modules, dataset bindings,
    and policy toggles.
    """

    model_config = ConfigDict(extra="forbid")

    profile_default: str = Field(
        default="default",
        description="Default profile name when none is specified.",
    )
    modules: list[str] = Field(
        default_factory=list,
        description=(
            "Ordered list of module names to load. "
            "Each name maps to modules/<name>.toml under CONFIDANTIC_ROOT."
        ),
    )
    datasets: dict[str, DatasetDeclaration] = Field(
        default_factory=dict,
        description="Named dataset declarations with path and record model.",
    )
    strict_jsonl: bool = Field(
        default=False,
        description=(
            "When True, any invalid JSONL line raises an error "
            "instead of warn-skip."
        ),
    )
    export_models: list[str] = Field(
        default_factory=list,
        description=(
            "Dotted import paths to Pydantic model classes that "
            "should be exported as CUE schemas."
        ),
    )
