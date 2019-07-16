import os
import sys
import uuid
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')  # noqa

from ciri import fields
from ciri.core import PolySchema as Schema, Schema as StandardSchema
from ciri.exception import ValidationError

import pytest


@pytest.mark.parametrize("value, expected", [
    [{'type_': 'a', 'foo': 'bar', 'bar': 'foo'}, {'type_': 'a', 'foo': 'bar'}],
    [{'type_': 'b', 'foo': 'bar', 'bar': 'foo'}, {'type_': 'b', 'bar': 'foo'}],
])
def test_polymorphism(value, expected):
    class Poly(Schema):

        type_ = fields.String(required=True)

        __poly_on__ = type_

    class PolyA(Poly):
        __poly_id__ = 'a'

        foo = fields.String(required=True)

    class PolyB(Poly):
        __poly_id__ = 'b'

        bar = fields.String(required=True)

    schema = Poly()
    assert schema.serialize(value) == expected 


@pytest.mark.parametrize("value, expected", [
    [{'type_': 'a', 'foo': 'bar', 'bar': 'foo'}, {'type_': 'a', 'foo': 'bar'}],
    [{'type_': 'b', 'foo': 'bar', 'bar': 'foo'}, {'type_': 'b', 'bar': 'foo'}],
])
def test_polymorphism_encode(value, expected):
    class Poly(Schema):
        type_ = fields.String(required=True)
        __poly_on__ = type_

    class PolyA(Poly):
        __poly_id__ = 'a'

        foo = fields.String(required=True)

    class PolyB(Poly):
        __poly_id__ = 'b'

        bar = fields.String(required=True)

    schema = Poly()
    assert json.loads(schema.encode(value)) == json.loads(json.dumps(expected))


def test_polymorphism_deserialization():
    class Poly(Schema):
        type_ = fields.String(required=True)
        __poly_on__ = type_

    class PolyA(Poly):
        __poly_id__ = 'a'

        foo = fields.String(required=True)

    class PolyB(Poly):
        __poly_id__ = 'b'

        bar = fields.String(required=True)

    schema = Poly()
    expected = {'type_': 'a', 'foo': 'bar'}
    deserialized = schema.deserialize({'type_': 'a', 'foo': 'bar', 'bar': 'foo'})
    assert deserialized == PolyA(**expected)


def test_subclass_poly_attrs():
    class Poly(Schema):
        __poly_attrs__ = ['foo']

        type_ = fields.String(required=True)
        __poly_on__ = type_

        def foo(self, data):
            return 'foo{}'.format(data)

    class PolyA(Poly):
        __poly_id__ = 'a'

        bar = fields.String(required=True)

    schema = PolyA()
    assert schema.foo('bar') == 'foobar'


@pytest.mark.parametrize("value, expected", [
    [{'type_': 'a', 'foo': 'bar', 'bar': 'foo'}, 'Poly'],
    [{'type_': 'b', 'foo': 'bar', 'bar': 'foo'}, 'Poly'],
])
def test_polymorph_base_type(value, expected):
    class Poly(Schema):

        type_ = fields.String(required=True)

        __poly_on__ = type_

    class PolyA(Poly):
        __poly_id__ = 'a'

        foo = fields.String(required=True)

    class PolyB(Poly):
        __poly_id__ = 'b'

        bar = fields.String(required=True)

    assert type(Poly(**value)).__name__ == expected 


@pytest.mark.parametrize("value, expected", [
    [{'type_': 'a', 'foo': 'bar', 'bar': 'foo'}, 'PolyA'],
    [{'type_': 'b', 'foo': 'bar', 'bar': 'foo'}, 'PolyB'],
])
def test_polymorph_method_type(value, expected):
    class Poly(Schema):

        type_ = fields.String(required=True)

        __poly_on__ = type_

    class PolyA(Poly):
        __poly_id__ = 'a'

        foo = fields.String(required=True)

    class PolyB(Poly):
        __poly_id__ = 'b'

        bar = fields.String(required=True)

    assert type(Poly.polymorph(**value)).__name__ == expected 


@pytest.mark.parametrize("value, expected", [
    [{'type_': 'a', 'foo': 'bar', 'bar': 'foo'}, 'PolyA'],
    [{'type_': 'b', 'foo': 'bar', 'bar': 'foo'}, 'PolyB'],
])
def test_polymorph_deserialize_type(value, expected):
    class Poly(Schema):

        type_ = fields.String(required=True)

        __poly_on__ = type_

    class PolyA(Poly):

        class Meta:
            poly_id = 'a'

        foo = fields.String(required=True)

    class PolyB(Poly):
        __poly_id__ = 'b'

        bar = fields.String(required=True)

    assert type(Poly().deserialize(value)).__name__ == expected 


def test_list_base_poly_deserialize():
    class Poly(Schema):

        type_ = fields.String(required=True)

        __poly_on__ = type_

    class PolyA(Poly):

        class Meta:
            poly_id = 'a'

        foo = fields.String(required=True)

    class PolyB(Poly):
        __poly_id__ = 'b'

        bar = fields.String(required=True)


    class PolyList(StandardSchema):

        polys = fields.List(Poly())


    schema = PolyList(polys=[
        {'type_': 'a', 'foo': 'bar'},
        {'type_': 'b', 'bar': 'foo'}
    ])

    poly_list = schema.deserialize()

    types = (type(poly_list.polys[0]), type(poly_list.polys[1]),)
    assert types == (PolyA, PolyB,)


def test_list_poly_deserialize():
    class Poly(Schema):

        type_ = fields.String(required=True)

        __poly_on__ = type_

    class PolyA(Poly):

        class Meta:
            poly_id = 'a'

        foo = fields.String(required=True)

    class PolyB(Poly):
        __poly_id__ = 'b'

        bar = fields.String(required=True)


    class PolyList(StandardSchema):

        polys = fields.List(PolyA())


    schema = PolyList(polys=[
        {'type_': 'a', 'foo': 'bar'},
        {'type_': 'a', 'foo': 'hoo'}
    ])

    poly_list = schema.deserialize()
    types = (type(poly_list.polys[0]), type(poly_list.polys[1]),)
    assert types == (PolyA, PolyA,)


def test_list_poly_options():
    class Poly(Schema):

        type_ = fields.String(required=True)
        hello = fields.String()

        __poly_on__ = type_

    class PolyA(Poly):

        class Meta:
            poly_id = 'a'

        foo = fields.String(required=True)
        footest = fields.String(required=True)

    class PolyB(Poly):
        __poly_id__ = 'b'

        bar = fields.String(required=True)
        bartest = fields.String(required=True)


    class PolyList(StandardSchema):

        polys = fields.List(fields.Schema(Poly, exclude=['footest', 'bartest']))


    #PolyA(type_='a', foo='bar'),
    #PolyB(type_='b', bar='foo')

    schema = PolyList(polys=[
        {'type_': 'a', 'foo': 'bar'},
        {'type_': 'b', 'bar': 'foo'},
    ])

    data = schema.serialize() 
    assert data == {'polys': [{'type_': 'a', 'foo': 'bar'}, {'type_': 'b', 'bar': 'foo'}]}


def test_poly_instance_mapping():
    class PolyTest1(Schema):

        type = fields.String(required=True)

        __poly_on__ = type

    class PolyA(PolyTest1):

        class Meta:
            poly_id = 'a'

        foo = fields.String(required=True)

    class PolyB(PolyTest1):
        __poly_id__ = 'b'

        bar = fields.String(required=True)


    class PolyTest2(Schema):

        version = fields.Integer(required=True)

        __poly_on__ = version


    class PolyC(PolyTest2):

        class Meta:
            poly_id = 'c'

        foo = fields.String(required=True)

    class PolyD(PolyTest2):

        class Meta:
            poly_id = 'd'

        bar = fields.String(required=True)
        



    a = {'type': 'a', 'foo': 'bar'}
    b = {'type': 'b', 'bar': 'foo'}
    c = {'version': 'c', 'foo': 'bar'}
    d = {'version': 'd', 'bar': 'foo'}

    sa = PolyTest1.polymorph(**a)
    sb = PolyTest1.polymorph(**b)
    sc = PolyTest2.polymorph(**c)
    sd = PolyTest2.polymorph(**d)

    data = {
        'sa': type(sa),
        'sb': type(sb),
        'sc': type(sc),
        'sd': type(sd),
    }


    expected = {
        'sa': PolyA,
        'sb': PolyB,
        'sc': PolyC,
        'sd': PolyD,
    }

    assert data == expected 


def test_poly_sub_serialization():

    class Poly(Schema):
        type = fields.String(required=True)
        __poly_on__ = type


    class PolyA(Poly):
        class Meta:
            poly_id = 'a'
        foo = fields.String(required=True)

    class PolyB(Poly):
        __poly_id__ = 'b'
        bar = fields.String(required=True)

    
    class Sub(StandardSchema):
        
        poly = fields.Schema(Poly)


    a = Sub().serialize({'poly': {'type': 'a', 'foo': 'bar'}})
    b = Sub().serialize({'poly': {'type': 'b', 'bar': 'foo'}})

    assert {'a': a, 'b': b} == {'a': {'poly': {'type': 'a', 'foo': 'bar'}}, 'b': {'poly': {'type': 'b', 'bar': 'foo'}}}


def test_poly_sub_serialization_missing():

    class Poly(Schema):
        type = fields.String(required=True)
        __poly_on__ = type


    class PolyA(Poly):
        class Meta:
            poly_id = 'a'
        foo = fields.String(required=True)

    
    class Sub(StandardSchema):
        
        poly = fields.Schema(Poly, allow_none=True)


    a = Sub().serialize({})

    assert {} == {}


def test_poly_sub_serialization_invalid():

    class Poly(Schema):
        type = fields.String(required=True)
        __poly_on__ = type


    class PolyA(Poly):
        class Meta:
            poly_id = 'a'
        foo = fields.String(required=True)

    
    class Sub(StandardSchema):
        
        poly = fields.Schema(Poly)

    
    errors = {'poly': {'msg': fields.Schema(Poly).message.invalid_polykey}}

    schema = Sub(poly={'a': 'b'})
    with pytest.raises(ValidationError):
        schema.serialize({})
    assert schema.errors == errors


def test_poly_deserialize_with_dynamic_load():
    class S(Schema):
        first_name = fields.String()
        type = fields.String(load='field_type', name='ftype', required=True)
        __poly_on__ = type

    class SUser(S):
        class Meta:
            poly_id = 'user'
        last_name = fields.String()

    expected = {'first_name': 'foo', 'last_name': 'bar', 'field_type': 'user'}
    schema = S()
    s = schema.deserialize(expected)
    assert s == SUser(type='user', **expected)


def test_poly_sub_deserialization_on_sub_schema():
    carJSON = json.dumps({
        "info": {
            "n_brands": 2,
            "brands": [
                { "label": "TSLA", "desc": "Tesla" },
                { "label": "F", "desc": "Ford" }
            ]
        }
    })

    class CarBrand(StandardSchema):
        label = fields.String(required=True)
        desc = fields.String(required=True)

    class DealershipCarBrands(StandardSchema):
        n_brands = fields.Float(required=True)
        brands = fields.List(CarBrand(), required=True)

    class Dealership(StandardSchema):
        info = fields.Schema(DealershipCarBrands, required=True)

    dealer = Dealership()
    dic = dealer.deserialize(json.loads(carJSON))
    assert isinstance(dic.info.brands[0], CarBrand)

def test_poly_sub_serialization_on_sub_schema():

    class TestSchema2(Schema):
        sub_type = fields.String(required=True)
        __poly_on__ = sub_type

    class TestSchema1(Schema):
        type = fields.String(required=True)
        __poly_on__ = type
        sub_schema = fields.Schema(TestSchema2, required=True)

    class TestSchema2a(TestSchema2):
        __poly_id__ = 'sub_type'
        test = fields.String()

    class TestSchema1a(TestSchema1):
        __poly_id__ = 'type'
        test = fields.String()

    test_input = {'sub_schema': { 'sub_type': 'sub_type', 'test': 'a' }, 'type': 'type', 'test': 'b' }

    result = TestSchema1a().deserialize(test_input)

    s = TestSchema1a().serialize(result)

    assert s == test_input
