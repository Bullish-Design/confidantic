"""CUE source emitters — transform Pydantic model schema to CUE definitions."""

from __future__ import annotations

from typing import Any, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from confidantic.cue_export.naming import field_name_to_cue, python_type_to_cue


def emit_cue_definition(
    model_cls: type[BaseModel],
    *,
    package_name: str = "confidantic",
) -> str:
    """Generate a CUE definition string from a Pydantic model class.

    Returns a complete CUE file content including package declaration.
    """
    lines: list[str] = []
    lines.append(f"package {package_name}")
    lines.append("")
    lines.append(f"#{ model_cls.__name__}: {{")

    for field_name, field_info in model_cls.model_fields.items():
        cue_field = field_name_to_cue(field_name)
        cue_type = _resolve_cue_type(field_info)
        optional = not field_info.is_required()

        if optional:
            cue_field = f"{cue_field}?"
        lines.append(f"\t{cue_field}: {cue_type}")

    lines.append("}")
    lines.append("")

    return "\n".join(lines)


def _resolve_cue_type(field_info: FieldInfo) -> str:
    """Resolve a Pydantic FieldInfo annotation to a CUE type expression."""
    annotation = field_info.annotation
    if annotation is None:
        return "_"

    return _type_to_cue(annotation)


def _type_to_cue(annotation: Any) -> str:
    """Convert a Python type annotation to a CUE type string."""
    origin = get_origin(annotation)

    # Handle Optional[X] (Union[X, None])
    if origin is type(None):
        return "null"

    # Handle list[X]
    if origin is list:
        args = get_args(annotation)
        if args:
            inner = _type_to_cue(args[0])
            return f"[...{inner}]"
        return "[...]"

    # Handle dict[K, V]
    if origin is dict:
        args = get_args(annotation)
        if len(args) >= 2:
            key_type = _type_to_cue(args[0])
            val_type = _type_to_cue(args[1])
            return f"{{[{key_type}]: {val_type}}}"
        return "{...}"

    # Handle Union types
    if _is_union(origin):
        args = get_args(annotation)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1 and len(args) == 2:
            # Optional[X] -> X | null
            inner = _type_to_cue(non_none[0])
            return f"null | {inner}"
        if non_none:
            parts = [_type_to_cue(a) for a in non_none]
            return " | ".join(parts)
        return "_"

    # Handle Pydantic model references
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return f"#{annotation.__name__}"

    # Handle plain types
    if isinstance(annotation, type):
        return python_type_to_cue(annotation.__name__)

    return "_"


def _is_union(origin: Any) -> bool:
    """Check if a type origin is a Union."""
    import types

    if origin is type(None):
        return False
    # Python 3.10+ union syntax (X | Y)
    if isinstance(origin, type) and origin.__name__ == "UnionType":
        return True
    if origin is getattr(types, "UnionType", None):
        return True
    # typing.Union
    import typing

    return origin is typing.Union
