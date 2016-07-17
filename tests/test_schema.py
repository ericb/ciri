import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')

from ciri import fields
from ciri.core import Schema


def test_basic_serialization():
    class Test(Schema):
        pass

    schema = Test()
    assert schema.serialize({})._data == {}
    assert not schema.errors


def test_basic_validation():
    class Test(Schema):
        pass

    schema = Test()
    assert schema.validate({}).errors == {}


def test_string_validation():
    class Test(Schema):
        label = fields.String()

    schema = Test()
    errors = {'label': {'message': fields.String().message.invalid }}

    assert schema.serialize({'label': 'hello world'})._data == {'label': 'hello world'}
    assert not schema.errors

    assert schema.serialize({'label': '4'})._data == {'label': '4'}
    assert not schema.errors

    assert schema.serialize({'label': None})._data == {}
    assert schema.errors == errors

    assert schema.serialize({'label': 5})._data == {}
    assert schema.errors == errors

    assert schema.serialize({'label': {}})._data == {}
    assert schema.errors == errors

    assert schema.serialize({'label': []})._data == {}
    assert schema.errors == errors


def test_integer_validation():
    class Test(Schema):
        count = fields.Integer()

    schema = Test()
    errors = {'count': {'message': fields.Integer().message.invalid }}

    assert schema.serialize({'count': 5})._data == {'count': 5}
    assert not schema.errors

    assert schema.serialize({'count': 99999999999})._data == {'count': 99999999999}
    assert not schema.errors

    assert schema.serialize({'count': True})._data == {}
    assert schema.errors == errors

    assert schema.serialize({'count': '5'})._data == {}
    assert schema.errors == errors

    assert schema.serialize({'count': {}})._data == {}
    assert schema.errors == errors

    assert schema.serialize({'count': []})._data == {}
    assert schema.errors == errors

    assert schema.serialize({'count': None})._data == {}
    assert schema.errors == errors

    assert schema.serialize({'count': 50.3})._data == {}
    assert schema.errors == errors

"""
def test_boolean_validation():
    class Test(Schema):
        active = fields.Boolean()

    test_a = Test(active=False)
    test_b = Test(active=True)
    test_c = Test(active=3)
    test_d = Test(active='True')
    test_e = Test(active={})
    test_f = Test(active=[])
    test_g = Test(active=None)

    invalid_msg = fields.Boolean().message.invalid
    active_invalid_error = {'active': {'message': invalid_msg}}

    assert test_a.serialize()._data == {'active': False}
    assert not test_a.errors

    assert test_b.serialize()._data == {'active': True}
    assert not test_b.errors

    assert test_c.serialize()._data == {}
    assert test_c.errors == active_invalid_error

    assert test_d.serialize()._data == {}
    assert test_d.errors == active_invalid_error

    assert test_e.serialize()._data == {}
    assert test_e.errors == active_invalid_error

    assert test_f.serialize()._data == {}
    assert test_f.errors == active_invalid_error

    assert test_g.serialize()._data == {}
    assert test_g.errors == active_invalid_error


def test_dict_validation():
    class Test(Schema):
        mapping = fields.Dict()

    test_a = Test(mapping={'foo': 'bar'})
    test_b = Test(mapping={'foo': Test})
    test_c = Test(mapping={})
    test_d = Test(mapping=dict(foo='bar'))
    test_e = Test(mapping=None)
    test_f = Test(mapping=4)
    test_g = Test(mapping=True)

    invalid_msg = fields.Dict().message.invalid
    mapping_invalid_error = {'mapping': {'message': invalid_msg}}

    assert test_a.serialize()._data == {'mapping': {'foo': 'bar'}}
    assert not test_a.errors

    assert test_b.serialize()._data == {'mapping': {'foo': Test}}
    assert not test_b.errors

    assert test_c.serialize()._data == {'mapping': {}}
    assert not test_c.errors

    assert test_d.serialize()._data == {'mapping': {'foo': 'bar'}}
    assert not test_d.errors

    assert test_e.serialize()._data == {}
    assert test_e.errors == mapping_invalid_error

    assert test_f.serialize()._data == {}
    assert test_f.errors == mapping_invalid_error

    assert test_g.serialize()._data == {}
    assert test_g.errors == mapping_invalid_error


def test_list_validation():
    class Test(Schema):
        fruits = fields.List()

    test_a = Test(fruits=['apple', 'orange', 'strawberry'])
    test_b = Test(fruits=[])
    test_c = Test(fruits=list(('apple',)))
    test_d = Test(fruits=[False])
    test_e = Test(fruits=[1,2,3])
    test_f = Test(fruits=[[1,2]])
    test_g = Test(fruits=None)
    test_h = Test(fruits={'apple', 'orange'})
    test_i = Test(fruits=True)
    test_j = Test(fruits=5)
    test_k = Test(fruits=fields.String())

    invalid_msg = fields.List().message.invalid
    invalid_string_msg = fields.String().message.invalid
    invalid_item_msg = fields.List().message.invalid_item
    fruits_invalid_error = {'fruits': {'message': invalid_msg}}
    fruits_invalid_item_error = {'fruits': {'message': invalid_item_msg, 'errors': {'0': {'message': invalid_string_msg}}}}

    assert test_a.serialize()._data == {'fruits': ['apple', 'orange', 'strawberry']}
    assert not test_a.errors

    assert test_b.serialize()._data == {'fruits': []}
    assert not test_b.errors

    assert test_c.serialize()._data == {'fruits': ['apple']}
    assert not test_c.errors

    assert test_d.serialize()._data == {}
    assert test_d.errors == fruits_invalid_item_error

    assert test_e.serialize()._data == {}
    assert test_e.errors == {'fruits': {
        'message': invalid_item_msg, 
        'errors': {
            '0': {
                'message': invalid_string_msg
            },
            '1': {
                'message': invalid_string_msg
            },
            '2': {
                'message': invalid_string_msg
            }
        }
    }}

    assert test_f.serialize()._data == {}
    assert test_f.errors == fruits_invalid_item_error

    assert test_g.serialize()._data == {}
    assert test_g.errors == fruits_invalid_error

    assert test_h.serialize()._data == {}
    assert test_h.errors == fruits_invalid_error

    assert test_i.serialize()._data == {}
    assert test_i.errors == fruits_invalid_error

    assert test_j.serialize()._data == {}
    assert test_j.errors == fruits_invalid_error

    assert test_k.serialize()._data == {}
    assert test_k.errors == fruits_invalid_error


def test_default_value():
    class Test(Schema):
        active = fields.Boolean(default=True)

    test = Test()
    assert test.serialize()._data == {'active': True}
    assert not test.errors


def test_required_field():
    class Test(Schema):
        name = fields.String(required=True)

    test = Test()
    assert test.serialize().errors == {'name': 'Required Field'}
    assert test._data == {}


def test_allow_none_field():
    class Test(Schema):
        age = fields.Integer(allow_none=True)

    test = Test(name=2)
    assert test.serialize()._data == {'age': None}
    assert not test.errors


def test_multiple_invalid_fields():
    class Test(Schema):
        name = fields.String(required=True)
        age = fields.Integer(required=True)

    test = Test(name=2, age='thirteen')
    assert test.serialize().errors == {'name': {'message': 'Field is not a valid String'}, 
                                       'age': {'message': 'Field is not a valid Integer'}}
"""
