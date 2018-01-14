import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')  # noqa

from ciri.fields import String, Schema as SubSchema
from ciri.core import Schema
from ciri.registry import SchemaRegistry, schema_registry
from ciri.exception import RegistryError

import pytest


def test_default_registry():
    class S(Schema):
        foo = String()
    schema_registry.add('test', S)
    assert schema_registry.get('test') == S


def test_registry_default():
    assert schema_registry.get('__doesnotexist__', default=None) == None


def test_registry_reset():
    schema_registry.reset()
    assert schema_registry.get('test', default=None) == None


def test_registry_error():
    with pytest.raises(RegistryError):
        schema_registry.get('__doesnotexist__')


def test_custom_registry():
    class FooSchema(Schema):
        bar = String()
    reg = SchemaRegistry()
    reg.add('foo', FooSchema)
    
    class S(Schema):
        foo = SubSchema('foo', registry=reg)
    schema = S()
    
    assert schema.serialize({'foo': {'bar': 'hello world'}}) == {'foo': {'bar': 'hello world'}}
