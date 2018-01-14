import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')  # noqa

from ciri.fields import Integer, Float
from ciri.core import Schema
from ciri.exception import ValidationError

import pytest


def test_non_strict_float_validation():
    class N(Schema):
        num = Float(strict=False)
    schema = N()
    schema.validate({'num': 1})
    assert not schema.raw_errors


def test_non_strict_float_serialization():
    class N(Schema):
        num = Float(strict=False)
    schema = N()
    assert schema.serialize({'num': 1}) == {'num': 1.00}


@pytest.mark.parametrize("value", [
    1.00,
    '1',
    True,
    False,
    {},
    [],
    {'bar1', 'bar2'},
    Schema
])
def test_invalid_int_values(value):
    class N(Schema):
        num = Integer()
    schema = N()
    with pytest.raises(ValidationError):
        schema.serialize({'num': value})
    assert schema.raw_errors['num'].message == Integer().message.invalid


@pytest.mark.parametrize("value", [
    1,
    '1',
    True,
    False,
    {},
    [],
    {'bar1', 'bar2'},
    Schema
])
def test_invalid_float_values(value):
    class N(Schema):
        num = Float()
    schema = N()
    with pytest.raises(ValidationError):
        schema.serialize({'num': value})
    assert schema.raw_errors['num'].message == Float().message.invalid
