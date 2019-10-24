import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')  # noqa

from ciri import fields
from ciri.fields import FieldError
from ciri.core import Schema, SchemaOptions
from ciri.registry import SchemaRegistry, schema_registry
from ciri.exception import ValidationError, SerializationError, FieldValidationError

import pytest


def test_default_value():
    class S(Schema):
        active = fields.Boolean(default=True, output_missing=True)
    schema = S()
    assert schema.serialize({}) == {'active': True}


def test_required_field():
    class S(Schema):
        name = fields.String(required=True)
    schema = S()
    with pytest.raises(ValidationError):
        schema.serialize({})
    assert schema._raw_errors['name'].message == fields.String().message.required


def test_required_field_with_allowed_none():
    class S(Schema):
        name = fields.String(required=True, allow_none=False)
    schema = S()
    with pytest.raises(ValidationError):
        schema.serialize({'name': None})
    assert schema._raw_errors['name'].message == fields.String().message.required


def test_required_field_with_allowed_none_as_true():
    class S(Schema):
        name = fields.String(required=True, allow_none=True)
    schema = S()
    assert schema.serialize({'name': None}) == {'name': None}


def test_allow_none_field():
    class S(Schema):
        age = fields.Integer(allow_none=True)
    schema = S()
    assert schema.serialize({'name': 2, 'age': None}) == {'age': None}


def test_allow_none_schema_field():
    class A(Schema):
        foo = fields.String(required=True)

    class S(Schema):
        age = fields.Integer(allow_none=True)
        other = fields.Schema(A, allow_none=True)

    schema = S()
    assert schema.serialize({'name': 2, 'other': None, 'age': None}) == {'age': None, 'other': None}


def test_missing_field_with_allow_none():
    class S(Schema):
        age = fields.Integer(allow_none=True)
    schema = S()
    assert schema.serialize({'name': 2, 'age': None}) == {'age': None}


def test_output_missing_mix():
    class S(Schema):
        class Meta:
            options = SchemaOptions(output_missing=True)
        a = fields.Integer(output_missing=True)
        b = fields.Integer()
        c = fields.Integer(output_missing=False)
    schema = S()
    assert schema.serialize({}) == {'a': None, 'b': None}


def test_missing_field_with_output_missing():
    class S(Schema):
        age = fields.Integer(output_missing=True)
    schema = S()
    assert schema.serialize({'name': 2}) == {'age': None}


def test_missing_field_with_output_missing_deserialization():
    class S(Schema):
        age = fields.Integer(output_missing=True)
    schema = S()
    assert schema.deserialize({'name': 2}).age == None


def test_output_missing_value():
    class S(Schema):
        age = fields.Integer(output_missing=True, missing_output_value=5)
    schema = S()
    assert schema.serialize({'name': 2}) == {'age': 5}


def test_output_missing_value_deserialization():
    class S(Schema):
        age = fields.Integer(output_missing=True, missing_output_value=5)
    schema = S()
    assert schema.deserialize({'name': 2}).age == 5 


def test_no_halt_on_error():
    class S(Schema):
        name = fields.String(required=True)
        age = fields.Integer(required=True)

    schema = S()
    with pytest.raises(ValidationError):
        schema.validate()
    assert len(schema.errors) == 2


def test_halt_on_error():
    class S(Schema):
        name = fields.String(required=True)
        age = fields.Integer(required=True)

    schema = S()
    with pytest.raises(ValidationError):
        schema.validate(halt_on_error=True)
    assert len(schema.errors) == 1
