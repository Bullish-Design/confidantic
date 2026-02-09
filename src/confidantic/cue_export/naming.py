"""Naming conventions for CUE schema export.

Ensures generated file names are stable and don't churn unexpectedly.
"""

from __future__ import annotations

import re


def model_to_cue_filename(model_name: str) -> str:
    """Convert a Pydantic model class name to a CUE filename.

    E.g. "AppConfig" -> "app_config.cue"
    """
    # Convert CamelCase to snake_case
    s = re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", model_name)
    s = re.sub(r"(?<=[A-Z])([A-Z][a-z])", r"_\1", s)
    return s.lower() + ".cue"


def python_type_to_cue(type_name: str) -> str:
    """Map a Python/Pydantic type name to a CUE type expression."""
    mapping = {
        "str": "string",
        "int": "int",
        "float": "float",
        "bool": "bool",
        "NoneType": "null",
        "SecretStr": "string",
        "SecretBytes": "bytes",
        "Path": "string",
        "datetime": "string",
        "date": "string",
        "time": "string",
        "UUID": "string",
        "AnyUrl": "string",
        "EmailStr": "string",
    }
    return mapping.get(type_name, "_")


def field_name_to_cue(field_name: str) -> str:
    """Ensure a field name is valid CUE syntax.

    CUE field names that are valid identifiers are used as-is.
    Others get quoted.
    """
    if re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", field_name):
        return field_name
    return f'"{field_name}"'
