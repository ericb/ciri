import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')  # noqa

from ciri.fields import String, Schema as SubSchema
from ciri.core import Schema
from ciri.exception import ValidationError

import pytest


class FooSchema(Schema):
    a = String(required=True)


def test_schema_validation():
    class S(Schema):
        foo = SubSchema(FooSchema)
    schema = S()
    with pytest.raises(ValidationError):
        schema.validate({'foo': {}})
    assert schema._raw_errors['foo'].errors['a'].message == String().message.required


def test_schema_validation():
    class S(Schema):
        foo = SubSchema(FooSchema)
    schema = S()
    with pytest.raises(ValidationError):
        schema.validate({'foo': {}})
    assert schema._raw_errors['foo'].errors['a'].message == String().message.required


def test_schema_serialization():
    class S(Schema):
        foo = SubSchema(FooSchema)
    schema = S()
    assert schema.serialize({'foo': {'a': 'b'}}) == {'foo': {'a': 'b'}}
