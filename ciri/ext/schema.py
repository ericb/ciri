from abc import ABCMeta

from ciri.core import AbstractBaseSchema, Schema
from ciri.compat import add_metaclass
from ciri.exception import SerializationError


class AbstractPolySchema(AbstractBaseSchema):

    def __new__(cls, name, bases, attrs):
        klass = super(AbstractPolySchema, cls).__new__(cls, name, bases, attrs) 
        poly = bases[0]
        if '__poly_on__' in attrs:
            poly.__poly_mapping__ = {}
        if '__poly_id__' in attrs:
            attrs.update(poly._fields)
            for a in getattr(poly, '__poly_attrs__', []):
                attrs[a] = getattr(poly, a)
            klass = AbstractBaseSchema.__new__(cls, name, (Schema,) + bases[1:], attrs) 
            poly.__poly_mapping__[attrs['__poly_id__']] = klass
        return klass


@add_metaclass(AbstractPolySchema)
class PolySchema(Schema):

    def deserialize(self, data=None, *args, **kwargs):
        ident_key = self.__poly_on__
        data = data or self
        if hasattr(data, '__dict__'):
            data = vars(data)
        id_ = data.get(ident_key)
        if not id_:
            raise SerializationError
        schema = self.__poly_mapping__.get(id_)()
        return schema.deserialize(data, *args, **kwargs)

    def serialize(self, data=None, *args, **kwargs):
        ident_key = self.__poly_on__
        data = data or self
        if hasattr(data, '__dict__'):
            data = vars(data)
        id_ = data.get(ident_key)
        if not id_:
            raise SerializationError
        schema = self.__poly_mapping__.get(id_)()
        return schema.serialize(data, *args, **kwargs)

    def encode(self, data=None, *args, **kwargs):
        ident_key = self.__poly_on__
        data = data or self
        if hasattr(data, '__dict__'):
            data = vars(data)
        id_ = data.get(ident_key)
        if not id_:
            raise SerializationError
        schema = self.__poly_mapping__.get(id_)()
        return schema.encode(data, *args, **kwargs)
