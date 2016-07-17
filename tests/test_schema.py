import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')

from ciri import fields
from ciri.core import Schema


def test_basic_serialization():
    class Test(Schema):
        pass

    schema = Test()
    assert schema.serialize({}) == {}
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

    assert schema.serialize({'label': 'hello world'}) == {'label': 'hello world'}
    assert not schema.errors

    assert schema.serialize({'label': '4'}) == {'label': '4'}
    assert not schema.errors

    assert schema.serialize({'label': None}) == {}
    assert schema.errors == errors

    assert schema.serialize({'label': 5}) == {}
    assert schema.errors == errors

    assert schema.serialize({'label': {}}) == {}
    assert schema.errors == errors

    assert schema.serialize({'label': []}) == {}
    assert schema.errors == errors


def test_integer_validation():
    class Test(Schema):
        count = fields.Integer()

    schema = Test()
    errors = {'count': {'message': fields.Integer().message.invalid }}

    assert schema.serialize({'count': 5}) == {'count': 5}
    assert not schema.errors

    assert schema.serialize({'count': 99999999999}) == {'count': 99999999999}
    assert not schema.errors

    assert schema.serialize({'count': True}) == {}
    assert schema.errors == errors

    assert schema.serialize({'count': '5'}) == {}
    assert schema.errors == errors

    assert schema.serialize({'count': {}}) == {}
    assert schema.errors == errors

    assert schema.serialize({'count': []}) == {}
    assert schema.errors == errors

    assert schema.serialize({'count': None}) == {}
    assert schema.errors == errors

    assert schema.serialize({'count': 50.3}) == {}
    assert schema.errors == errors


def test_boolean_validation():
    class Test(Schema):
        active = fields.Boolean()

    schema = Test()
    errors = {'active': {'message': fields.Boolean().message.invalid}}

    assert schema.serialize({'active': False}) == {'active': False}
    assert not schema.errors

    assert schema.serialize({'active': True}) == {'active': True}
    assert not schema.errors

    assert schema.serialize({'active': 3}) == {}
    assert schema.errors == errors

    assert schema.serialize({'active': 'True'}) == {}
    assert schema.errors == errors

    assert schema.serialize({'active': {}}) == {}
    assert schema.errors == errors

    assert schema.serialize({'active': []}) == {}
    assert schema.errors == errors

    assert schema.serialize({'active': None}) == {}
    assert schema.errors == errors


def test_dict_validation():
    class Test(Schema):
        mapping = fields.Dict()

    schema = Test()
    errors = {'mapping': {'message': fields.Dict().message.invalid}}

    assert schema.serialize({'mapping': {'foo': 'bar'}}) == {'mapping': {'foo': 'bar'}}
    assert not schema.errors

    assert schema.serialize({'mapping': {'foo': Test}}) == {'mapping': {'foo': Test}}
    assert not schema.errors

    assert schema.serialize({'mapping': {}}) == {'mapping': {}}
    assert not schema.errors

    assert schema.serialize({'mapping': dict(foo='bar')}) == {'mapping': {'foo': 'bar'}}
    assert not schema.errors

    assert schema.serialize({'mapping': None}) == {}
    assert schema.errors == errors

    assert schema.serialize({'mapping': 4}) == {}
    assert schema.errors == errors

    assert schema.serialize({'mapping': True}) == {}
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

    assert schema.serialize({'fruits': ['apple', 'orange', 'strawberry']}) == {'fruits': ['apple', 'orange', 'strawberry']}
    assert not schema.errors

    assert schema.serialize({'fruits': []}) == {'fruits': []}
    assert not schema.errors

    assert schema.serialize({'fruits': list(('apple',))}) == {'fruits': ['apple']}
    assert not schema.errors

    assert schema.serialize({'fruits': [False]}) == {}
    assert schema.errors == fruits_items_errors

    assert schema.serialize({'fruits': [1,2,3]}) == {}
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

    assert schema.serialize({'fruits': [[1,2]]}) == {}
    assert schema.errors == fruits_items_errors

    assert schema.serialize({'fruits': None}) == {}
    assert schema.errors == fruits_errors

    assert schema.serialize({'fruits': {'apple', 'orange'}}) == {}
    assert schema.errors == fruits_errors

    assert schema.serialize({'fruits': True}) == {}
    assert schema.errors == fruits_errors

    assert schema.serialize({'fruits': 5}) == {}
    assert schema.errors == fruits_errors

    assert schema.serialize({'fruits': fields.String()}) == {}
    assert schema.errors == fruits_errors

def test_default_value():
    class Test(Schema):
        active = fields.Boolean(default=True)

    schema = Test()
    assert schema.serialize({}) == {'active': True}
    assert not schema.errors


def test_required_field():
    class Test(Schema):
        name = fields.String(required=True)

    schema = Test()
    assert schema.serialize({}).errors == {'name': 'Required Field'}
    assert schema == {}


def test_allow_none_field():
    class Test(Schema):
        age = fields.Integer(allow_none=True)

    schema = Test()
    assert schema.serialize({'name': 2})._data == {'age': None}
    assert not schema.errors


def test_multiple_invalid_fields():
    class Test(Schema):
        name = fields.String(required=True)
        age = fields.Integer(required=True)

    errors = {'name': {'message': 'Field is not a valid String'},
              'age': {'message': 'Field is not a valid Integer'}}

    schema = Test()
    assert schema.serialize({'name': 2, 'age': 'thirteen'}).errors == errors
