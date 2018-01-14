from abc import ABCMeta

from ciri.abstract import AbstractField, AbstractBaseSchema, SchemaFieldDefault, SchemaFieldMissing
from ciri.compat import add_metaclass
from ciri.registry import schema_registry
from ciri.exception import InvalidSchemaException, SchemaException, SerializationException, RegistryError, ValidationError, FieldValidationError


class FieldError(object):

    def __init__(self, field_cls, field_msg_key, errors=None, *args, **kwargs):
        self.field = field_cls
        self.message_key = field_msg_key
        self.message = field_cls.message[field_msg_key]
        self.errors = errors


class FieldErrorMessages(object):

    def __init__(self, *args, **kwargs):
        self._messages = {
            'invalid': 'Invalid Field',
            'required': 'Required Field'
        }
        self._messages.update(kwargs)


class FieldMessageContainer(object):

    def __init__(self, field):
        self._field = field

    def __getattr__(self, name):
        if self._field._messages.get(name):
            return self._field_messages[name]
        else:
            return self._field.messages._messages[name]

    def __getitem__(self, name):
        if self._field._messages.get(name):
            return self._field_messages[name]
        else:
            return self._field.messages._messages[name]


class AbstractBaseField(ABCMeta):

    def __new__(cls, name, bases, attrs):
        klass = ABCMeta.__new__(cls, name, bases, dict(attrs))
        if isinstance(attrs.get('messages'), FieldErrorMessages):
            klass.messages = attrs.get('messages')
        else:
            klass.messages = FieldErrorMessages(**attrs.get('messages', {}))
        if getattr(klass, 'new', None):
            constructor = klass.__init__
            new_constructor = klass.new

            def field_init(self, *args, **kwargs):
                constructor(self, *args, **kwargs)
                new_constructor(self, *args, **kwargs)

            klass.__init__ = field_init
            delattr(klass, 'new')
        return klass


@add_metaclass(AbstractBaseField)
class Field(AbstractField):

    def __init__(self, *args, **kwargs):
        self.name = kwargs.get('name', None)
        self.required = kwargs.get('required', False)
        self.default = kwargs.get('default', SchemaFieldDefault)
        self.allow_none = kwargs.get('allow_none', False)
        self._messages = kwargs.get('messages', {})
        self.message = FieldMessageContainer(self)

    def serialize(self, value):
        raise NotImplementedError

    def validate(self, value):
        raise NotImplementedError


class String(Field):

    messages = {'invalid': 'Field is not a valid String',
                'empty': 'Field cannot be empty'}

    def new(self, *args, **kwargs):
        self.allow_empty = kwargs.get('allow_empty', True)
        self.trim = kwargs.get('trim', True)

    def serialize(self, value):
        if isinstance(value, str):
            return str(value)
        raise SerializationException

    def validate(self, value):
        if not isinstance(value, str) or str(value) != value:
            raise FieldValidationError(FieldError(self, 'invalid'))
        if self.trim:
            value = value.strip() 
        if value == '' and not self.allow_empty:
            raise FieldValidationError(FieldError(self, 'empty'))



class Integer(Field):

    messages = {'invalid': 'Field is not a valid Integer'}

    def serialize(self, value):
        if isinstance(value, int) and type(value) == int:
            return value
        raise SerializationException

    def validate(self, value):
        if not isinstance(value, int) or (type(value) != int):
            raise FieldValidationError(FieldError(self, 'invalid'))


class Float(Field):

    messages = {'invalid': 'Field is not a valid Float'}

    def new(self, *args, **kwargs):
        self.strict = kwargs.get('strict', True)  # allow integers to be passed and converted to a float

    def serialize(self, value):
        if isinstance(value, float) and type(value) == float:
            return value
        elif not self.strict and isinstance(value, int):
           return float(value)
        raise SerializationException

    def validate(self, value):
        if not self.strict and isinstance(value, int):
           value = float(value)
        if not isinstance(value, float) or (type(value) != float):
            raise FieldValidationError(FieldError(self, 'invalid'))


class Boolean(Field):

    def serialize(self, value):
        if isinstance(value, bool) and type(value) == bool:
            if value:
                return True
            return False
        raise SerializationException

    def validate(self, value):
        if not isinstance(value, bool) or (type(value) != bool):
            raise FieldValidationError(FieldError(self, 'invalid'))


class Dict(Field):

    def serialize(self, value):
        if isinstance(value, dict):
            return value
        raise SerializationException

    def validate(self, value):
        if not isinstance(value, dict):
            raise FieldValidationError(FieldError(self, 'invalid'))


class List(Field):

    messages = {'invalid_item': 'Invalid Value'}

    def new(self, *args, **kwargs):
        self.field = kwargs.get('of', String())
        self.items = kwargs.get('items', [])

    def serialize(self, value):
        data = []
        for k, v in enumerate(value):
            try:
                value = self.field.serialize(v)
                data.append(value)
            except SerializationException:
                pass
        return data

    def validate(self, value):
        errors = {}
        if not isinstance(value, list):
            raise FieldValidationError(FieldError(self, 'invalid'))
        for k, v in enumerate(value):
            try:
                self.field.validate(v)
            except FieldValidationError as field_exc:
                errors[str(k)] = field_exc.error
        if errors:
            raise FieldValidationError(FieldError(self, 'invalid_item', errors=errors))


class Schema(Field):

    messages = {'invalid': 'Invalid Schema'}

    def new(self, schema, *args, **kwargs):
        self.registry = kwargs.get('registry', schema_registry)
        self.raw_schema = schema
        self.schema = schema
        if not isinstance(self.schema, AbstractBaseSchema):
            self.schema = self.registry.get(schema, default=None)

    def _get_schema(self):
        if not self.schema:
           self.schema = self.registry.get(self.raw_schema)
        return self.schema

    def serialize(self, value):
        schema = self._get_schema()()
        return schema.serialize(value)

    def validate(self, value):
        schema = self._get_schema()()
        try:
            schema.validate(value)
        except ValidationError as e:
            raise FieldValidationError(FieldError(self, 'invalid', errors=schema._raw_errors))
