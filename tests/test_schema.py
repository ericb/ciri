import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')  # noqa

from ciri.fields import Boolean, String, List, Schema as SubSchema
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


def test_nested_schema_validation():
    class S(Schema):
        foo = SubSchema(FooSchema, required=True)

    class Node(Schema):
        label = String(required=True)
        sub = SubSchema(S, required=True)

    class Root(Schema):
        node = SubSchema(Node, required=True)

    schema = Root()
    with pytest.raises(ValidationError):
        schema.validate({
            'node': {
                'label': 'test',
                'sub': {
                    'foo': {}
                }
            }
        })
    assert schema._raw_errors['node'].errors['sub'].errors['foo'].errors['a'].message == String().message.required


def test_halt_on_sub_errors():
    class Node(Schema):
        tags = List(required=True)

    class Root(Schema):
        node = SubSchema(Node, required=True)

    schema = Root(node=Node(tags=[1,2]))
    with pytest.raises(ValidationError):
        schema.validate(halt_on_error=True)
    assert len(schema._raw_errors['node'].errors['tags'].errors) == 1


def test_subschema_pre_serializer():
    def upper(value, **kwargs):
        return value.replace(' ', '_').upper()

    class Node(Schema):
        label = String(required=True)
        id = String(pre_serialize=[upper])

    class Root(Schema):
        node = SubSchema(Node, required=True)
        enabled = Boolean(default=False)

    schema = Root()
    assert schema.serialize({'node': {'label': 'foo bar', 'id': 'foo bar'}}) == {'enabled': False, 'node': {'label': 'foo bar', 'id': 'FOO_BAR'}}
