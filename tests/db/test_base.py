"""
Tests for db.base: uuid4_str().
"""
import uuid

from monsterforge.db.base import uuid4_str


def test_uuid4_str_returns_a_valid_uuid4_string():
    value = uuid4_str()

    assert isinstance(value, str)
    assert uuid.UUID(value).version == 4


def test_uuid4_str_returns_a_different_value_each_call():
    assert uuid4_str() != uuid4_str()
