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
    assert schema.raw_errors['foo'].message == String().message.empty


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
    assert schema.raw_errors['foo'].message == String().message.invalid
