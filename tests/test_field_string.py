import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')  # noqa

from ciri.fields import String
from ciri.core import Schema
from ciri.exception import ValidationError

import pytest


def test_empty():
    class S(Schema):
        foo = String()
    schema = S()
    assert schema.serialize({'foo': ''}) == {'foo': ''}
    assert not schema.errors


def test_not_allowed_empty():
    class S(Schema):
        foo = String(allow_empty=False)
    schema = S()
    with pytest.raises(ValidationError):
        schema.serialize({'foo': ''})
    assert schema._raw_errors['foo'].message == String().message.empty

def test_not_allowed_empty_with_whitespace():
    class S(Schema):
        foo = String(allow_empty=False)
    schema = S()
    with pytest.raises(ValidationError):
        schema.serialize({'foo': ' '})
    assert schema._raw_errors['foo'].message == String().message.empty


@pytest.mark.parametrize("value", [
    1,
    True,
    False,
    {},
    [],
    {'bar1', 'bar2'},
    Schema
])
def test_invalid_values(value):
    class S(Schema):
        foo = String()
    schema = S()
    with pytest.raises(ValidationError):
        schema.serialize({'foo': value})
    assert schema._raw_errors['foo'].message == String().message.invalid


@pytest.mark.parametrize("value, expected", [
    ['hello', 'hello'],
    [str('testing'), 'testing']
])
def test_deserialization(value, expected):
    class S(Schema):
        foo = String()
    schema = S()
    assert schema.deserialize({'foo': value}) == S(foo=expected)
