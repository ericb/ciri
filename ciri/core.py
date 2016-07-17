from ciri.abstract import AbstractField, SchemaFieldDefault, SchemaFieldMissing
from ciri.exception import SchemaException, SerializationException


class MetaSchema(type):

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

    def __init__(cls, name, bases, attrs):
        cls._data = {}


class Schema(metaclass=MetaSchema):

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            if self._fields.get(k):
                setattr(self, k, kwargs[k])

    def __setattr__(self, k, v):
        if self._fields.get(k):
            self._elements[k] = True
        super().__setattr__(k, v)

    def _parse_errors(self, exc):
        data = {'message': str(exc)}
        if hasattr(exc, '_errors'):
            data['errors'] = {}
            for k, v in exc._errors.items():
                data['errors'][str(k)] = self._parse_errors(v);
        return data

    def validate(self):
        self.errors = {}
        for key in self._elements.keys():
            klass_value = getattr(self, key, SchemaFieldMissing)
            if (klass_value == SchemaFieldMissing) and (self._fields[key].default is not SchemaFieldDefault):
                klass_value = self._fields[key].default
            if self._fields[key].required and (klass_value == SchemaFieldMissing):
                self.errors[key] = self._fields[key].message.required
            elif self._fields[key].allow_none and (klass_value == SchemaFieldMissing):
                pass
            else:
                try:
                    self._fields[key].validate(klass_value)
                except SchemaException as e:
                    self.errors[key] = self._parse_errors(e);
        return self

    def serialize(self, skip_validation=False):
        
        self._data = {}
        if not skip_validation:
            self.validate()
        for key in self._elements.keys():
            klass_value = getattr(self, key, SchemaFieldMissing)
            if (klass_value == SchemaFieldMissing) and (self._fields[key].default is not SchemaFieldDefault):
                klass_value = self._fields[key].default
            name = self._fields[key].name
            if name is None:
                name = key
            if self._fields[key].allow_none and (klass_value == SchemaFieldMissing):
                self._data[name] = None
            else:
                if not self.errors.get(key, None):
                    try:
                        value = self._fields[key].serialize(klass_value)
                        if klass_value != SchemaFieldMissing:
                            self._data[name] = value
                    except SerializationException:
                        pass
        return self

