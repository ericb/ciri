import os
import sys
import uuid
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')  # noqa

from ciri import fields
from ciri.core import PolySchema as Schema
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
