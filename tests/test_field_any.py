import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')  # noqa

from ciri.fields import Float, Integer, String, Any, Anything
from ciri.core import Schema
from ciri.exception import ValidationError

import pytest


def test_valid_anything():
    class A(Schema):
        a = Anything([Float(), String()])
        b = Anything([Float(), String()])
    schema = A()
    assert schema.serialize({'a': 5.0, 'b': 'Five'}) == {'a': 5.0, 'b': 'Five'}

def test_valid_any():
    class A(Schema):
        a = Any([Float(), String()])
        b = Any([Float(), String()])
    schema = A()
    assert schema.serialize({'a': 5.0, 'b': 'Five'}) == {'a': 5.0, 'b': 'Five'}

def test_invalid_any():
    class A(Schema):
        a = Any([Float(strict=True), String()])
    schema = A()
    errors = {'a': {'msg': 'Invalid Field'}}
    with pytest.raises(ValidationError):
        schema.serialize({'a': 33})
    assert schema.errors == errors

def test_deserialize_valid_any():
    class A(Schema):
        a = Any([Float(), String()])
        b = Any([Float(), String()])
    schema = A()
    assert schema.deserialize({'a': 5.0, 'b': 'Five'}) == A(a=5.0, b='Five')
