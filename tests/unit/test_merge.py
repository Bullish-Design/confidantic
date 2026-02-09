"""Tests for the deterministic merge engine."""

from pydantic import BaseModel, Field

from confidantic.core.merge import deep_merge, get_list_policy


class TestDeepMergeBasic:
    def test_scalar_replace(self):
        left = {"a": 1, "b": "hello"}
        right = {"a": 2}
        result = deep_merge(left, right)
        assert result == {"a": 2, "b": "hello"}

    def test_dict_deep_merge(self):
        left = {"a": {"x": 1, "y": 2}, "b": 10}
        right = {"a": {"y": 3, "z": 4}}
        result = deep_merge(left, right)
        assert result == {"a": {"x": 1, "y": 3, "z": 4}, "b": 10}

    def test_list_replace_by_default(self):
        left = {"tags": [1, 2, 3]}
        right = {"tags": [4, 5]}
        result = deep_merge(left, right)
        assert result == {"tags": [4, 5]}

    def test_empty_dicts(self):
        assert deep_merge({}, {}) == {}

    def test_left_only_keys(self):
        result = deep_merge({"a": 1}, {})
        assert result == {"a": 1}

    def test_right_only_keys(self):
        result = deep_merge({}, {"a": 1})
        assert result == {"a": 1}

    def test_nested_deep_merge(self):
        left = {"a": {"b": {"c": 1, "d": 2}}}
        right = {"a": {"b": {"c": 3, "e": 4}}}
        result = deep_merge(left, right)
        assert result == {"a": {"b": {"c": 3, "d": 2, "e": 4}}}

    def test_type_mismatch_right_wins(self):
        left = {"a": {"x": 1}}
        right = {"a": "string"}
        result = deep_merge(left, right)
        assert result == {"a": "string"}

    def test_key_ordering_is_stable(self):
        left = {"c": 1, "a": 2}
        right = {"b": 3}
        result = deep_merge(left, right)
        assert list(result.keys()) == ["a", "b", "c"]


class TestListPolicies:
    def test_get_list_policy_default(self):
        assert get_list_policy(None) == "replace"

    def test_append_policy(self):
        class M(BaseModel):
            tags: list[str] = Field(
                default_factory=list,
                json_schema_extra={"list_merge": "append"},
            )

        result = deep_merge(
            {"tags": ["a", "b"]},
            {"tags": ["c"]},
            schema=M,
        )
        assert result == {"tags": ["a", "b", "c"]}

    def test_unique_policy(self):
        class M(BaseModel):
            tags: list[str] = Field(
                default_factory=list,
                json_schema_extra={"list_merge": "unique"},
            )

        result = deep_merge(
            {"tags": ["a", "b"]},
            {"tags": ["b", "c"]},
            schema=M,
        )
        assert result == {"tags": ["a", "b", "c"]}

    def test_keyed_policy(self):
        class M(BaseModel):
            items: list[dict] = Field(
                default_factory=list,
                json_schema_extra={"list_merge": "keyed:name"},
            )

        left = {"items": [{"name": "x", "val": 1}, {"name": "y", "val": 2}]}
        right = {"items": [{"name": "x", "val": 10}, {"name": "z", "val": 3}]}
        result = deep_merge(left, right, schema=M)

        names = [item["name"] for item in result["items"]]
        assert names == ["x", "y", "z"]
        # x should have been merged (right val wins)
        x_item = next(i for i in result["items"] if i["name"] == "x")
        assert x_item["val"] == 10

    def test_replace_policy_explicit(self):
        class M(BaseModel):
            tags: list[str] = Field(
                default_factory=list,
                json_schema_extra={"list_merge": "replace"},
            )

        result = deep_merge(
            {"tags": ["a", "b"]},
            {"tags": ["c"]},
            schema=M,
        )
        assert result == {"tags": ["c"]}


class TestMergeImmutability:
    def test_original_dicts_not_modified(self):
        left = {"a": {"x": 1}}
        right = {"a": {"y": 2}}
        result = deep_merge(left, right)
        assert left == {"a": {"x": 1}}
        assert right == {"a": {"y": 2}}
        assert result == {"a": {"x": 1, "y": 2}}
