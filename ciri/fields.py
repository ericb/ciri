import datetime
import re
from abc import ABCMeta

from ciri.abstract import AbstractField, AbstractSchema, SchemaFieldDefault, SchemaFieldMissing
from ciri.compat import add_metaclass
from ciri.registry import schema_registry
from ciri.exception import InvalidSchemaException, SchemaException, SerializationException, RegistryError, ValidationError, FieldValidationError
from ciri.util.dateparse import parse_date, parse_datetime


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
        self._schema = None

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
                self.field._schema = self._schema
                self.field.validate(v)
            except FieldValidationError as field_exc:
                errors[str(k)] = field_exc.error
                if self.field._schema._validation_opts.get('halt_on_error'):
                    break
        if errors:
            raise FieldValidationError(FieldError(self, 'invalid_item', errors=errors))


class Schema(Field):

    messages = {'invalid': 'Invalid Schema'}

    def new(self, schema, *args, **kwargs):
        self.registry = kwargs.get('registry', schema_registry)
        self.raw_schema = schema
        self.cached = None
        self.schema = schema
        subclass = False
        try:
            if issubclass(self.schema, AbstractSchema):
                subclass = True
        except TypeError:
            pass
        if not subclass:
            self.schema = self.registry.get(schema, default=None)
            if self.schema:
                self.cached = self.schema()
        else:
            self.cached = self.schema()

    def _get_schema(self):
        if not self.cached:
           self.schema = self.registry.get(self.raw_schema)
           self.cached = self.schema()
        return self.cached

    def serialize(self, value):
        schema = self.cached or self._get_schema()
        return schema.serialize(value)

    def validate(self, value):
        schema = self.cached or self._get_schema()
        try:
            schema._schema = self._schema
            schema.validate(value, **schema._schema._validation_opts)
        except ValidationError as e:
            raise FieldValidationError(FieldError(self, 'invalid', errors=schema._raw_errors))


class Date(Field):

    messages = {'invalid': 'Invalid ISO-8601 Date'}

    def serialize(self, value):
        if isinstance(value, str):
            try:
                dt = parse_datetime(value)
            except (ValueError, TypeError):
                dt = None

            if not dt:
                try:
                    dt = parse_date(value)
                except (ValueError, TypeError):
                    dt = None

            if not dt:
                return value
            else:
                value = dt

        if isinstance(value, datetime.date):
            value = datetime.datetime(value.year, value.month, value.day)
        return value.isoformat('_').split('_')[0]

    def validate(self, value):
        if isinstance(value, datetime.date) or isinstance(value, datetime.datetime):
            return

        try:
            dt = parse_datetime(value)
        except (ValueError, TypeError):
            dt = None

        if not dt:
            try:
                dt = parse_date(value)
            except (ValueError, TypeError):
                raise FieldValidationError(FieldError(self, 'invalid'))

        if dt:
            return dt
        raise FieldValidationError(FieldError(self, 'invalid'))


class DateTime(Field):

    messages = {'invalid': 'Invalid ISO-8601 DateTime'}

    def serialize(self, value):
        if isinstance(value, str):
            return parse_datetime(value).isoformat()
        return value.isoformat()

    def validate(self, value):
        if isinstance(value, datetime.date):
            return
        try:
            dt = parse_datetime(value)
            if dt:
                return dt
            raise FieldValidationError(FieldError(self, 'invalid'))
        except (ValueError, TypeError):
            raise FieldValidationError(FieldError(self, 'invalid'))
