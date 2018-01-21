import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')  # noqa

from ciri.fields import Boolean
from ciri.core import Schema
from ciri.exception import ValidationError

import pytest


@pytest.mark.parametrize("value", [
    1,
    '1',
    {},
    [],
    {'bar1', 'bar2'},
    Schema
])
def test_invalid_values(value):
    class B(Schema):
        foo = Boolean()
    schema = B()
    with pytest.raises(ValidationError):
        schema.serialize({'foo': value})
    assert schema._raw_errors['foo'].message == Boolean().message.invalid


@pytest.mark.parametrize("value, expected", [
    [False, False],
    [True, True]
])
def test_deserialization(value, expected):
    class B(Schema):
        foo = Boolean()
    schema = B()
    assert schema.deserialize({'foo': value}) == B(foo=expected)
