import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')  # noqa

from ciri.fields import Boolean, Float, String, List, Schema as SubSchema, SelfReference
from ciri.core import Schema, PolySchema, SchemaOptions
from ciri.exception import ValidationError
from ciri.registry import schema_registry

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
        enabled = Boolean(default=False, output_missing=True)

    schema = Root()
    assert schema.serialize({'node': {'label': 'foo bar', 'id': 'foo bar'}}) == {'enabled': False, 'node': {'label': 'foo bar', 'id': 'FOO_BAR'}}


def test_subschema_as_none():
    class Node(Schema):
        label = String(required=True)
        id = String()

    class Root(Schema):
        node = SubSchema(Node, allow_none=True)
        enabled = Boolean(default=False)

    schema = Root()
    assert schema.serialize({'node': None}) == {'node': None}

def test_subschema_deserialize_as_none():
    class Node(Schema):
        pass

    class Root(Schema):
        node = SubSchema(Node, allow_none=True)
        enabled = Boolean(default=False)

    schema = Root()
    assert schema.deserialize({'node': None}) == Root(node=None)

def test_subrecursive_serialize_self():

    class Node(Schema):
        id = String(required=True)
        node = SelfReference(allow_none=True)

    class Root(PolySchema):
        node = SubSchema(Node, allow_none=True)
        enabled = Boolean(default=False)
        category = String(required=True)

        __poly_on__ = category

    class Foo(Root):

        __poly_id__ = 'foo'

    schema = Root()
    assert schema.serialize({'node': {'id': '1', 'node': {'id': '2', 'node': None}}, 'enabled': True, 'category': 'foo'}) == Foo(node=Node(id='1', node=Node(id='2', node=None)), enabled=True, category='foo').serialize()


def test_subrecursive_deserialize_self():

    class Node(Schema):
        id = String(required=True)
        node = SelfReference(allow_none=True)

    class Root(Schema):
        node = SubSchema(Node, allow_none=True)
        enabled = Boolean(default=False)

    schema = Root()
    assert schema.deserialize({'node': {'id': '1', 'node': {'id': '2', 'node': None}}}) == Root(node=Node(id='1', node=Node(id='2', node=None)))


def test_subschema_as_object():
    class Node(Schema):
        id = String(required=True)
        label = String()

    class Root(Schema):
        node = SubSchema(Node, allow_none=True)
        enabled = Boolean(default=False)

    root = Root().deserialize({'node': {'id': '1', 'label': 'Testing'}, 'enabled': False})
    assert root.node.id == '1'

def test_list_subschema_as_object():
    class Stuff(Schema):
        id = String(required=True)
        label = String()

    class Node(Schema):
        id = String(required=True)
        label = String()
        nodes = List(SubSchema(Stuff, allow_none=True))

    class Root(Schema):
        nodes = List(SubSchema(Node, allow_none=True))
        enabled = Boolean(default=False)

    root = Root().deserialize({'nodes': [{'id': '1', 'label': 'Testing', 'nodes': [{'id': '2', 'label': 'Hi'}] }], 'enabled': False})
    assert root.nodes[0].id == '1'


def test_subschema_list_of_sub_as_objects():

    class CarBrand(Schema):
        label = String(required=True)
        desc = String(required=True)

    class DealershipCarBrands(Schema):
        n_brands = Float(required=True)
        brands = List(SubSchema(CarBrand), required=True)

    class Dealership(Schema):
        info = SubSchema(DealershipCarBrands, required=True)

    car_dict = {
        "info": {
            "n_brands": 2,
            "brands": [
                { "label": "TSLA", "desc": "Tesla" },
                { "label": "F", "desc": "Ford" }
            ]
        }
    }

    dealership = Dealership().deserialize(car_dict)
    assert dealership.info.brands[1].label == 'F'

def test_schema_field_with_name():
    class Node(Schema):
        id = String(required=True)
        label = String()

    class Root(Schema):
        node = SubSchema(Node, name="foo_node", allow_none=False)
        enabled = Boolean(default=False)

    root = Root().deserialize({'node': {'id': '1', 'label': 'Testing'}, 'enabled': False})
    root_output = Root().serialize(root)
    assert root_output['foo_node'] == {'id': '1', 'label': 'Testing'}


def test_missing_schema_field():
    class Node(Schema):
        id = String()
        label = String()

    class Root(Schema):
        node = SubSchema(Node, name="foo_node", allow_none=True)
        enabled = Boolean(default=False)

    root = Root().deserialize({'enabled': False})
    root_output = Root().serialize(root)
    assert root_output == {'enabled': False}


def test_missing_schema_field_with_output_missing():
    class Node(Schema):
        id = String()
        label = String()

    class Root(Schema):
        node = SubSchema(Node, allow_none=True, output_missing=True)
        enabled = Boolean(default=False)

    root = Root().deserialize({'enabled': False})
    root_output = Root().serialize(root)
    assert root_output == {'enabled': False, 'node': None}


def test_missing_schema_field_with_name_and_output_missing():
    class Node(Schema):
        id = String()
        label = String()

    class Root(Schema):
        node = SubSchema(Node, name='foo_node', allow_none=True, output_missing=True)
        enabled = Boolean(default=False)

    root = Root().deserialize({'enabled': False})
    root_output = Root().serialize(root)
    assert root_output == {'enabled': False, 'foo_node': None}


def test_schema_field_with_default_callable():
    class Node(Schema):
        class Meta:
            options = SchemaOptions(output_missing=True)

        id = String()
        label = String()

    def make_subschema(schema, field):
        return field.schema().serialize({})

    class Root(Schema):
        node = SubSchema(Node, name="foo_node", default=make_subschema, output_missing=True)
        enabled = Boolean(default=False)

    root = Root().deserialize({'enabled': False})
    root_output = Root().serialize(root)
    assert root_output['foo_node'] == {'id': None, 'label': None}


def test_subrecursive_serialize_list():

    class Node(Schema):
        id = String(required=True)
        node = List(SubSchema('Node'), allow_none=True)

    schema_registry.add('Node', Node)

    schema = Node()
    assert schema.serialize({'id': '1', 'node': [{'id': '2', 'node': None}]}) == {'node': [{'id': '2', 'node': None}], 'id': '1'}
