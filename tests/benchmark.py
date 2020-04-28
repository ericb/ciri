import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')  # noqa


from ciri import fields
from ciri.core import PolySchema as Schema, Schema as StandardSchema, SchemaOptions
from ciri.exception import ValidationError, SerializationError

from timeit import default_timer as timer


class NestedNode(StandardSchema):

    foo = fields.SelfReference()
    foo_nested1 = fields.String()
    foo_nested2 = fields.String()
    foo_nested3 = fields.String()
    foo_nested4 = fields.String()
    foo_nested5 = fields.String()
    foo_nested6 = fields.String()
    foo_nested7 = fields.String()
    foo_nested8 = fields.String()
    foo_nested9 = fields.String()
    foo_nested10 = fields.String()
    foo_nested11 = fields.String()
    foo_nested12 = fields.String()
    foo_nested13 = fields.String()
    foo_nested14 = fields.String()
    foo_nested15 = fields.String()
    foo_nested16 = fields.String()
    foo_nested17 = fields.String()
    foo_nested18 = fields.String()
    foo_nested19 = fields.String()
    foo_nested20 = fields.String()
    foo_nested21 = fields.String()
    foo_nested22 = fields.String()
    foo_nested23 = fields.String()
    foo_nested24 = fields.String()
    foo_nested25 = fields.String()
    foo_nested26 = fields.String()
    foo_nested27 = fields.String()
    foo_nested28 = fields.String()
    foo_nested29 = fields.String()
    foo_nested30 = fields.String()
    foo_nested31 = fields.String()
    foo_nested32 = fields.String()
    foo_nested33 = fields.String()
    foo_nested34 = fields.String()
    foo_nested35 = fields.String()
    foo_nested36 = fields.String()
    foo_nested37 = fields.String()
    foo_nested38 = fields.String()
    foo_nested39 = fields.String()
    foo_nested40 = fields.String()
    foo_nested41 = fields.String()
    foo_nested42 = fields.String()


class Poly(Schema):

    type_ = fields.String(required=True)
    hello = fields.String()

    __poly_on__ = type_

class PolyA(Poly):

    class Meta:
        poly_id = 'a'

    foo = fields.Schema(NestedNode, required=True)
    footest = fields.String(required=True)

class PolyB(Poly):
    __poly_id__ = 'b'

    bar = fields.String(required=True)
    bartest = fields.String(required=True)


class PolyList(StandardSchema):

    polys = fields.List(fields.Schema(Poly, exclude=['footest', 'bartest']))





if __name__ == '__main__':
    # run benchmark
    print("Running")

    ncalls = 50

    start = timer()

    for _ in range(ncalls):
        schema = PolyList(polys=[
            {'type_': 'a', 'foo': {'foo_nested42': 'yolo', 'foo': {'foo_nested42': 'yolo', 'foo': {'foo_nested42': 'yolo', 'foo': {'foo_nested42': 'yolo', 'foo': {'foo_nested42': 'yolo', 'foo': {'foo_nested42': 'yolo', 'foo': {'foo_nested42': 'yolo', 'foo': {'foo_nested42': 'yolo', 'foo': {'foo_nested42': 'yolo', 'foo': {'foo_nested42': 'yolo', 'foo': {'foo_nested42': 'yolo', 'foo': {'foo_nested42': 'yolo', 'foo': {'foo_nested42': 'yolo', 'foo': {'foo_nested42': 'yolo', 'foo': {'foo_nested42': 'yolo', 'foo': {'foo_nested42': 'yolo', 'foo': {'foo_nested42': 'yolo', 'foo': {'foo_nested42': 'yolo', 'foo': {'foo_nested42': 'yolo', 'foo': {'foo_nested42': 'yolo', 'foo': {'foo_nested42': 'yolo', 'foo': {'foo_nested42': 'yolo', 'foo': {'foo_nested42': 'yolo'}}}}}}}}}}}}}}}}}}}}}}}},
            {'type_': 'b', 'bar': 'foo'}, {'type_': 'b', 'bar': 'foo'}, {'type_': 'b', 'bar': 'foo'}, {'type_': 'b', 'bar': 'foo'}, {'type_': 'b', 'bar': 'foo'}, {'type_': 'b', 'bar': 'foo'}, {'type_': 'b', 'bar': 'foo'}, {'type_': 'b', 'bar': 'foo'}, {'type_': 'b', 'bar': 'foo'}, {'type_': 'b', 'bar': 'foo'}, {'type_': 'b', 'bar': 'foo'}, {'type_': 'b', 'bar': 'foo'}, {'type_': 'b', 'bar': 'foo'}, {'type_': 'b', 'bar': 'foo'}, {'type_': 'b', 'bar': 'foo'}, {'type_': 'b', 'bar': 'foo'}, {'type_': 'b', 'bar': 'foo'}, {'type_': 'b', 'bar': 'foo'}, {'type_': 'b', 'bar': 'foo'}, {'type_': 'b', 'bar': 'foo'}, {'type_': 'b', 'bar': 'foo'}, {'type_': 'b', 'bar': 'foo'}, {'type_': 'b', 'bar': 'foo'}, {'type_': 'b', 'bar': 'foo'}, {'type_': 'b', 'bar': 'foo'}
        ])

    end = timer()

    avg_duration = (end-start) / ncalls

    print("Average schema initialization duration over {} calls: {} seconds".format(ncalls, avg_duration))

    start = timer()

    for _ in range(ncalls):
        data = schema.serialize() 

    end = timer()

    avg_duration = (end-start) / ncalls

    print("Average schema serialization duration over {} calls: {} seconds".format(ncalls, avg_duration))

    print("Data len: {}".format(len(data['polys'])))
