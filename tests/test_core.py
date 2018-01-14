import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')  # noqa

from ciri import fields
from ciri.core import Schema
from ciri.registry import SchemaRegistry, schema_registry
from ciri.exception import ValidationError

import pytest


def test_empty_serialization():
    schema = Schema()
    schema.serialize({})
    assert schema.errors == {}


def test_empty_validation():
    schema = Schema()
    assert schema.validate({}).errors == {}


def test_default_value():
    class S(Schema):
        active = fields.Boolean(default=True)
    schema = S()
    assert schema.serialize({}) == {'active': True}


def test_required_field():
    class S(Schema):
        name = fields.String(required=True)
    schema = S()
    with pytest.raises(ValidationError):
        schema.serialize({})
    assert schema._raw_errors['name'].message == fields.String().message.required


def test_allow_none_field():
    class S(Schema):
        age = fields.Integer(allow_none=True)
    schema = S()
    assert schema.serialize({'name': 2}) == {'age': None}


def test_multiple_invalid_fields():
    class S(Schema):
        name = fields.String(required=True)
        age = fields.Integer(required=True)

    errors = {'name': {'message': fields.String().message.invalid},
              'age': {'message': fields.Integer().message.invalid}}

    schema = S()
    with pytest.raises(ValidationError):
        schema.serialize({'name': 33, 'age': '33'})
        assert schema.errors == errors


def test_schema_kwargs():
    class Sub(Schema):
        hello = fields.String(required=True)

    class S(Schema):
        name = fields.String(required=True)
        active = fields.Boolean()
        sub = fields.Schema(Sub)

    schema = S(name='ciri', active=True, sub=Sub(hello='testing'))
    assert schema.serialize() == {'name': 'ciri', 'active': True, 'sub': {'hello': 'testing'}}


def test_subclass_schema():
    class Person(Schema):
        name = fields.String()
        age = fields.Integer()

    class Parent(Person):
        child = fields.Schema(Person)

    child = Person(name='Sarah', age=17)
    father = Parent(name='Jack', age=52, child=child)

    assert father.serialize() == {'name': 'Jack', 'age': 52, 'child': {'name': 'Sarah', 'age': 17}}


def test_subclass_override_schema():
    class Person(Schema):
        name = fields.String(allow_empty=True)
        age = fields.Integer()

    class Parent(Person):
        name = fields.String(allow_empty=False)
        child = fields.Schema(Person)

    child = Person(name='', age=17)
    father = Parent(name='Jack', age=52, child=child)

    assert father.serialize() == {'name': 'Jack', 'age': 52, 'child': {'name': '', 'age': 17}}
