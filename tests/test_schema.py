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


def test_boolean_validation():
    class Test(Schema):
        active = fields.Boolean()

    schema = Test()
    errors = {'active': {'message': fields.Boolean().message.invalid}}

    assert schema.serialize({'active': False})._data == {'active': False}
    assert not schema.errors

    assert schema.serialize({'active': True})._data == {'active': True}
    assert not schema.errors

    assert schema.serialize({'active': 3})._data == {}
    assert schema.errors == errors

    assert schema.serialize({'active': 'True'})._data == {}
    assert schema.errors == errors

    assert schema.serialize({'active': {}})._data == {}
    assert schema.errors == errors

    assert schema.serialize({'active': []})._data == {}
    assert schema.errors == errors

    assert schema.serialize({'active': None})._data == {}
    assert schema.errors == errors


def test_dict_validation():
    class Test(Schema):
        mapping = fields.Dict()

    schema = Test()
    errors = {'mapping': {'message': fields.Dict().message.invalid}}

    assert schema.serialize({'mapping': {'foo': 'bar'}})._data == {'mapping': {'foo': 'bar'}}
    assert not schema.errors

    assert schema.serialize({'mapping': {'foo': Test}})._data == {'mapping': {'foo': Test}}
    assert not schema.errors

    assert schema.serialize({'mapping': {}})._data == {'mapping': {}}
    assert not schema.errors

    assert schema.serialize({'mapping': dict(foo='bar')})._data == {'mapping': {'foo': 'bar'}}
    assert not schema.errors

    assert schema.serialize({'mapping': None})._data == {}
    assert schema.errors == errors

    assert schema.serialize({'mapping': 4})._data == {}
    assert schema.errors == errors

    assert schema.serialize({'mapping': True})._data == {}
    assert schema.errors == errors


def test_list_validation():
    class Test(Schema):
        fruits = fields.List()

    schema = Test()
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

    fruits_errors = {'fruits': {'message': fields.List().message.invalid}}
    fruits_items_errors = {'fruits': {
        'message': fields.List().message.invalid_item,
        'errors': {'0': {'message': fields.String().message.invalid}}}
    }

    assert schema.serialize({'fruits': ['apple', 'orange', 'strawberry']})._data == {'fruits': ['apple', 'orange', 'strawberry']}
    assert not schema.errors

    assert schema.serialize({'fruits': []})._data == {'fruits': []}
    assert not schema.errors

    assert schema.serialize({'fruits': list(('apple',))})._data == {'fruits': ['apple']}
    assert not schema.errors

    assert schema.serialize({'fruits': [False]})._data == {}
    assert schema.errors == fruits_items_errors

    assert schema.serialize({'fruits': [1,2,3]})._data == {}
    assert schema.errors == {'fruits': {
        'message': fields.List().message.invalid_item, 
        'errors': {
            '0': {
                'message': fields.String().message.invalid
            },
            '1': {
                'message': fields.String().message.invalid
            },
            '2': {
                'message': fields.String().message.invalid
            }
        }
    }}

    assert schema.serialize({'fruits': [[1,2]]})._data == {}
    assert schema.errors == fruits_items_errors

    assert schema.serialize({'fruits': None})._data == {}
    assert schema.errors == fruits_errors

    assert schema.serialize({'fruits': {'apple', 'orange'}})._data == {}
    assert schema.errors == fruits_errors

    assert schema.serialize({'fruits': True})._data == {}
    assert schema.errors == fruits_errors

    assert schema.serialize({'fruits': 5})._data == {}
    assert schema.errors == fruits_errors

    assert schema.serialize({'fruits': fields.String()})._data == {}
    assert schema.errors == fruits_errors

"""
def test_default_value():
    class Test(Schema):
        active = fields.Boolean(default=True)

    schema = Test()
    assert schema.serialize({})._data == {'active': True}
    assert not schema.errors

def test_required_field():
    class Test(Schema):
        name = fields.String(required=True)

    schema = Test()
    assert schema.serialize({}).errors == {'name': 'Required Field'}
    assert schema._data == {}


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
