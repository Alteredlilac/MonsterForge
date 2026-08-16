"""
Tests for monsterforge.serialization.plain_data.to_plain().

Covers:
- primitives pass through unchanged
- enums reduce to their .value
- dataclasses reduce to a dict of their fields, recursively
- the "id" field is always skipped (random identity, not content)
- lists/tuples and nested dicts are handled recursively
- UUID values reduce to strings
"""
import uuid
from dataclasses import dataclass, field
from enum import Enum
from monsterforge.serialization.plain_data import to_plain


class Color(str, Enum):
    RED = "red"
    BLUE = "blue"


@dataclass(kw_only=True)
class Inner:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    color: Color
    value: int | None = None


@dataclass(kw_only=True)
class Outer:
    name: str
    inner: Inner
    tags: list[Color] = field(default_factory=list)


def test_primitives_pass_through_unchanged():
    assert to_plain("text") == "text"
    assert to_plain(42) == 42
    assert to_plain(3.14) == 3.14
    assert to_plain(True) is True
    assert to_plain(None) is None


def test_enum_reduces_to_its_value():
    assert to_plain(Color.RED) == "red"


def test_dataclass_reduces_to_a_dict_without_id():
    inner = Inner(color=Color.BLUE, value=5)

    assert to_plain(inner) == {"color": "blue", "value": 5}


def test_nested_dataclass_is_recursively_flattened():
    outer = Outer(name="thing", inner=Inner(color=Color.RED), tags=[Color.RED, Color.BLUE])

    assert to_plain(outer) == {
        "name": "thing",
        "inner": {"color": "red", "value": None},
        "tags": ["red", "blue"],
    }


def test_uuid_reduces_to_a_string():
    value = uuid.uuid4()
    assert to_plain(value) == str(value)


def test_plain_dict_is_recursively_flattened():
    assert to_plain({"a": Color.RED, "b": [Color.BLUE]}) == {"a": "red", "b": ["blue"]}
