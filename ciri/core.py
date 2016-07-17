from abc import ABCMeta

from ciri.abstract import AbstractField
from ciri.compat import add_metaclass
from ciri.exception import SchemaException, SerializationException


# Type Definitions
SchemaFieldDefault = type('SchemaFieldDefault', (object,), {})
SchemaFieldMissing = type('SchemaFieldMissing', (object,), {})


class MetaSchema(ABCMeta):

    def __new__(cls, name, bases, attrs):
        klass = type.__new__(cls, name, bases, dict(attrs))
        klass._elements = {}
        klass._fields = {}
        klass.errors = None
        for k, v in attrs.items():
            if isinstance(v, AbstractField):
                klass._fields[k] = v
                delattr(klass, k)
                if v.required or v.allow_none or (v.default is not SchemaFieldDefault):
                    klass._elements[k] = True
        return klass


@add_metaclass(MetaSchema)
class Schema(object):

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            if self._fields.get(k):
                setattr(self, k, kwargs[k])

    def __setattr__(self, k, v):
        if self._fields.get(k):
            self._elements[k] = True
        super(Schema, self).__setattr__(k, v)

    def _parse_errors(self, exc):
        data = {'message': str(exc)}
        if hasattr(exc, '_errors'):
            data['errors'] = {}
            for k, v in exc._errors.items():
                data['errors'][str(k)] = self._parse_errors(v)
        return data

    def validate(self, data):
        self.errors = {}

        elements = self._elements.copy()
        for k, v in data.items():
            if self._fields.get(k):
                elements[k] = True

        for key in elements.keys():
            # field value
            klass_value = data.get(key, SchemaFieldMissing)

            # if the field is missing, set the default value
            if (klass_value == SchemaFieldMissing) and (self._fields[key].default is not SchemaFieldDefault):
                klass_value = self._fields[key].default

            # if the field is missing, but it's required, set an error.
            # if a value of None is allowed and we do not have a field, skip validation
            # otherwise, validate the value
            if self._fields[key].required and (klass_value == SchemaFieldMissing):
                self.errors[key] = self._fields[key].message.required
            elif self._fields[key].allow_none and (klass_value == SchemaFieldMissing):
                pass
            else:
                try:
                    self._fields[key].validate(klass_value)
                except SchemaException as e:
                    self.errors[key] = self._parse_errors(e)
        return self

    def serialize(self, data, skip_validation=False):
        output = {}
        elements = self._elements.copy()
        for k, v in data.items():
            if self._fields.get(k):
                elements[k] = True

        if not skip_validation:
            self.validate(data)

        for key in elements.keys():
            # field value
            klass_value = data.get(key, SchemaFieldMissing)

            # if the field is missing, set the default value
            if (klass_value == SchemaFieldMissing) and (self._fields[key].default is not SchemaFieldDefault):
                klass_value = self._fields[key].default

            # determine the field result name
            name = self._fields[key].name
            if name is None:
                name = key

            # if it's allowed, and the field is missing, set the value to None
            if self._fields[key].allow_none and (klass_value == SchemaFieldMissing):
                output[name] = None
            else:
                # if we have something to work with, try and serialize it
                if not self.errors.get(key, None):
                    try:
                        value = self._fields[key].serialize(klass_value)
                        if klass_value != SchemaFieldMissing:
                            output[name] = value
                    except SerializationException:
                        pass
        return output
