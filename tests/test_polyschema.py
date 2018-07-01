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
