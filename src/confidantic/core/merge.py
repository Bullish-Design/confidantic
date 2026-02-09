"""Deterministic merge engine with per-field list policy support.

Merge semantics:
- dict/object: deep merge (recursive)
- scalar: replace (right wins)
- list: replace by default

Per-field list policies via Pydantic Field json_schema_extra:
- "replace" (default): right list replaces left
- "append": concatenate right onto left
- "unique": concatenate then deduplicate by value
- "keyed:<field>": merge list-of-dicts by a unique key field
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from pydantic.fields import FieldInfo

# Sentinel for "no list policy set"
_NO_POLICY = "replace"


def get_list_policy(field_info: FieldInfo | None) -> str:
    """Extract list merge policy from Pydantic field metadata.

    Looks for json_schema_extra={"list_merge": "<policy>"}.
    Returns "replace" if no policy is set.
    """
    if field_info is None:
        return _NO_POLICY
    extra = field_info.json_schema_extra
    if isinstance(extra, dict):
        return extra.get("list_merge", _NO_POLICY)
    return _NO_POLICY


def deep_merge(
    left: dict[str, Any],
    right: dict[str, Any],
    schema: type[BaseModel] | None = None,
) -> dict[str, Any]:
    """Deep-merge two dicts with deterministic key ordering.

    Args:
        left: Base configuration dict.
        right: Overlay configuration dict (takes precedence).
        schema: Optional Pydantic model class to extract field-level
                merge policies from.

    Returns:
        Merged dict with stable key ordering.
    """
    result: dict[str, Any] = {}

    all_keys = sorted(set(left.keys()) | set(right.keys()))

    for key in all_keys:
        left_val = left.get(key)
        right_val = right.get(key)

        if key not in right:
            result[key] = _deep_copy(left_val)
        elif key not in left:
            result[key] = _deep_copy(right_val)
        else:
            # Both sides have the key — merge based on type
            field_info = _get_field_info(schema, key)
            result[key] = _merge_values(left_val, right_val, field_info, schema)

    return result


def _merge_values(
    left: Any,
    right: Any,
    field_info: FieldInfo | None,
    parent_schema: type[BaseModel] | None,
) -> Any:
    """Merge two values according to type and field policy."""
    # If both are dicts, deep merge
    if isinstance(left, dict) and isinstance(right, dict):
        child_schema = _get_child_schema(parent_schema, field_info)
        return deep_merge(left, right, child_schema)

    # If both are lists, apply list policy
    if isinstance(left, list) and isinstance(right, list):
        return _merge_lists(left, right, field_info)

    # Scalar or type mismatch: right replaces left
    return _deep_copy(right)


def _merge_lists(
    left: list[Any],
    right: list[Any],
    field_info: FieldInfo | None,
) -> list[Any]:
    """Merge two lists according to the field's list policy."""
    policy = get_list_policy(field_info)

    if policy == "replace":
        return list(right)

    if policy == "append":
        return list(left) + list(right)

    if policy == "unique":
        seen: set[Any] = set()
        result: list[Any] = []
        for item in list(left) + list(right):
            # Use JSON repr for unhashable types
            key = _make_hashable(item)
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result

    if policy.startswith("keyed:"):
        key_field = policy.split(":", 1)[1]
        return _merge_keyed_lists(left, right, key_field)

    # Unknown policy — fall back to replace
    return list(right)


def _merge_keyed_lists(
    left: list[Any], right: list[Any], key_field: str
) -> list[Any]:
    """Merge two lists of dicts by a unique key field.

    Items from right override items from left that share the same key.
    Order: left items first (in order), then new right items.
    """
    index: dict[Any, Any] = {}
    order: list[Any] = []

    for item in left:
        if isinstance(item, dict) and key_field in item:
            key = item[key_field]
            index[key] = dict(item)
            order.append(key)
        else:
            order.append(id(item))
            index[id(item)] = item

    for item in right:
        if isinstance(item, dict) and key_field in item:
            key = item[key_field]
            if key in index and isinstance(index[key], dict):
                # Deep merge the matching items
                index[key] = deep_merge(index[key], item)
            else:
                index[key] = dict(item)
                order.append(key)
        else:
            order.append(id(item))
            index[id(item)] = item

    return [index[k] for k in order if k in index]


def _get_field_info(
    schema: type[BaseModel] | None, key: str
) -> FieldInfo | None:
    """Get Pydantic FieldInfo for a key from a schema, if available."""
    if schema is None:
        return None
    fields = schema.model_fields
    return fields.get(key)


def _get_child_schema(
    parent_schema: type[BaseModel] | None,
    field_info: FieldInfo | None,
) -> type[BaseModel] | None:
    """Attempt to extract a child BaseModel schema from a field's annotation."""
    if field_info is None:
        return None
    annotation = field_info.annotation
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation
    return None


def _deep_copy(value: Any) -> Any:
    """Create a deep copy of dicts and lists (shallow for scalars)."""
    if isinstance(value, dict):
        return {k: _deep_copy(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_deep_copy(item) for item in value]
    return value


def _make_hashable(item: Any) -> Any:
    """Convert an item to something hashable for deduplication."""
    if isinstance(item, dict):
        return tuple(sorted((k, _make_hashable(v)) for k, v in item.items()))
    if isinstance(item, list):
        return tuple(_make_hashable(i) for i in item)
    return item
