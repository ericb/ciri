import datetime
import uuid
import re
from abc import ABCMeta

from ciri.abstract import AbstractField, AbstractSchema, SchemaFieldDefault, SchemaFieldMissing, UseSchemaOption
from ciri.compat import add_metaclass, str_
from ciri.registry import schema_registry
from ciri.exception import InvalidSchemaException, SchemaException, SerializationError, RegistryError, ValidationError, FieldValidationError
from ciri.util.dateparse import parse_date, parse_datetime


class FieldError(object):

    def __init__(self, field_cls, field_msg_key=None, errors=None, *args, **kwargs):
        self.field = field_cls
        self.message_key = field_msg_key
        self.message = kwargs.get('message') or field_cls.message[field_msg_key]
        self.errors = errors


class FieldErrorMessages(object):

    def __init__(self, *args, **kwargs):
        self._messages = {
            'invalid': 'Invalid Field',
            'required': 'Required Field',
            'invalid_mapping': 'Field is not a valid Mapping'
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
    """Base Field Class that all other Fields extend from"""

    __slots__ = ['name', 'required', 'default', 'allow_none',
                 '_messages', 'message', '_schema', 'validators',
                 'pre_validate', 'pre_serialize', 'pre_deserialize',
                 'post_validate', 'post_serialize', 'post_deserialize',
                 'missing_output_value', 'tags']

    def __init__(self, *args, **kwargs):
        self.name = kwargs.get('name', None)
        self.required = kwargs.get('required', False)
        self.default = kwargs.get('default', SchemaFieldDefault)
        self.allow_none = kwargs.get('allow_none', UseSchemaOption)
        self._messages = kwargs.get('messages', {})
        self.message = FieldMessageContainer(self)
        self.output_missing = kwargs.get('output_missing', UseSchemaOption)
        self.missing_output_value = kwargs.get('missing_output_value', None)
        self.tags = kwargs.get('tags', [])

        callables = ['pre_validate', 'pre_serialize', 'pre_deserialize',
                     'post_validate', 'post_serialize', 'post_deserialize']
        for c in callables:
            self._set_callable(c, kwargs.get(c))

    def _set_callable(self, type_, value):
        if isinstance(value, list):
            setattr(self, type_, value)
        else:
            setattr(self, type_, [])

    def serialize(self, value, **kwargs):
        """
        Serialization method 

        :param value: value to be serialized as a basic python type
        :raises: SerializationError, NotImplementedError
        """
        raise NotImplementedError

    def deserialize(self, value):
        """
        Deserialization method 

        :param value: value to be deserialized as a basic python type
        :raises: SerializationError, NotImplementedError
        """
        raise NotImplementedError

    def validate(self, value):
        """
        Validation method

        :param value: value to be deserialized as a basic python type
        :returns: validated value
        :raises: SerializationError, NotImplementedError
        """
        raise NotImplementedError


class String(Field):

    __slots__ = ['allow_empty', 'trim']

    messages = {'invalid': 'Field is not a valid String',
                'empty': 'Field cannot be empty'}

    def new(self, *args, **kwargs):
        self.allow_empty = kwargs.get('allow_empty', True)
        self.trim = kwargs.get('trim', True)
        self.encoding = kwargs.get('unicode_enc', 'utf-8')

    def serialize(self, value, **kwargs):
        if str is not str_:
            return str_(value, self.encoding)
        return value

    def deserialize(self, value):
        if str is not str_:
            return str_(value, self.encoding)
        return value

    def validate(self, value):
        if str is not str_:
            if isinstance(value, str_) and str_(value) == value:
                value = str(value)
        if type(value) is not str or str(value) != value:
            raise FieldValidationError(FieldError(self, 'invalid'))
        if self.trim:
            value = value.strip() 
        if not value and not self.allow_empty:
            raise FieldValidationError(FieldError(self, 'empty'))
        return value


Str = String


class Integer(Field):

    messages = {'invalid': 'Field is not a valid Integer'}

    def serialize(self, value, **kwargs):
        return value

    def deserialize(self, value):
        return int(value)

    def validate(self, value):
        if type(value) is int:
            return value
        try:
            if not float(value).is_integer():
                raise FieldValidationError(FieldError(self, 'invalid'))
        except TypeError:
            raise FieldValidationError(FieldError(self, 'invalid'))
        try:
            if int(value) != value or type(value) is bool:
                raise FieldValidationError(FieldError(self, 'invalid'))
        except ValueError:
            raise FieldValidationError(FieldError(self, 'invalid'))
        return value


Int = Integer


class Float(Field):

    messages = {'invalid': 'Field is not a valid Float'}

    def new(self, *args, **kwargs):
        self.strict = kwargs.get('strict', False)  # allow integers to be passed and converted to a float

    def serialize(self, value, **kwargs):
        return value

    def deserialize(self, value):
        return float(value)

    def validate(self, value):
        if type(value) is float:
            return value
        if type(value) in (bool, str, str_):
            raise FieldValidationError(FieldError(self, 'invalid'))
        try:
           float(value) is value
        except TypeError:
            raise FieldValidationError(FieldError(self, 'invalid'))
        if self.strict:
            try:
                value.is_integer() 
            except AttributeError:
                raise FieldValidationError(FieldError(self, 'invalid'))
        return value


class Boolean(Field):

    def serialize(self, value, **kwargs):
        if value:
            return True
        return False

    def deserialize(self, value):
        return bool(value)

    def validate(self, value):
        if type(value) is not bool:
            raise FieldValidationError(FieldError(self, 'invalid'))
        return value


Bool = Boolean


class Dict(Field):

    def serialize(self, value, **kwargs):
        return value

    def deserialize(self, value):
        return dict(value)

    def validate(self, value):
        if not isinstance(value, dict):
            raise FieldValidationError(FieldError(self, 'invalid'))
        return value


class List(Field):

    __slots__ = ['field', 'items']

    messages = {'invalid_item': 'Invalid Item(s)'}

    def new(self, *args, **kwargs):
        self.field = None
        self.schema_list = False
        if len(args) > 0:
            self.field = args[0]
        kwarg_field = kwargs.get('of')
        if not self.field and not kwarg_field:
            self.field = String()
        elif not self.field and kwarg_field:
            self.field = kwarg_field
        if isinstance(self.field, AbstractSchema):
            self.schema_list = True
        elif not isinstance(self.field, AbstractField):
            raise ValueError("'of' field must be a subclass of AbstractField or AbstractSchema")
        self.items = kwargs.get('items', [])

    def serialize(self, value, **kwargs):
        return [self.field.serialize(v) for v in value]

    def deserialize(self, value):
        return [self.field.deserialize(v) for v in value]

    def validate(self, value):
        valid = []
        errors = {}
        if not isinstance(value, list):
            raise FieldValidationError(FieldError(self, 'invalid'))
        for k, v in enumerate(value):
            if self.schema_list:
                if not hasattr(v, '__dict__') and (type(v) is not dict or not isinstance(v, dict)):
                    errors[str(k)] = FieldError(self, 'invalid_mapping')
                    if self.field._schema._validation_opts.get('halt_on_error'):
                        break
                    continue
            try:
                valid.append(self.field.validate(v))
            except FieldValidationError as field_exc:
                errors[str(k)] = field_exc.error
                if self.field._schema._validation_opts.get('halt_on_error'):
                    break
        if errors:
            raise FieldValidationError(FieldError(self, 'invalid_item', errors=errors))
        return valid

    def __setattr__(self, k, v):
        if k == '_schema':
            if hasattr(self, 'field'):
                self.field._schema = v
        super(Field, self).__setattr__(k, v)


class Schema(Field):

    __slots__ = ['registry', 'raw_schema', 'cached', 'schema']

    messages = {'invalid': 'Invalid Schema',
                'invalid_mapping': 'Field is not a valid Schema Mapping type'}

    def new(self, schema, *args, **kwargs):
        self.registry = kwargs.get('registry', schema_registry)
        self.raw_schema = schema
        self.cached = None
        self.schema = schema
        self.exclude = kwargs.get('exclude', [])
        self.whitelist = kwargs.get('whitelist', [])
        self.tags = kwargs.get('tags', [])

    def _get_schema(self):
        if not self.cached:
            try:
                if issubclass(self.schema, AbstractSchema):
                    self.cached = self.schema()
            except TypeError:
                self.schema = self.registry.get(self.schema, default=None)
                if not self.schema:
                    self.schema = self.registry.get(self.raw_schema)
                self.cached = self.schema()
            self.cached._schema = self._schema
        return self.cached

    def serialize(self, value, **kwargs):
        schema = self.cached or self._get_schema()
        return schema.serialize(value, exclude=self.exclude, whitelist=self.whitelist, tags=self.tags)

    def deserialize(self, value):
        schema = self.cached or self._get_schema()
        return schema.__class__(**value)

    def validate(self, value):
        if not hasattr(value, '__dict__') and (type(value) is not dict or not isinstance(value, dict)):
            raise FieldValidationError(FieldError(self, 'invalid_mapping', errors=schema._raw_errors))
        schema = self.cached or self._get_schema()
        schema._raw_errors = {}
        schema._error_handler.reset()
        try:
            return schema.validate(value, **schema._schema._validation_opts)
        except ValidationError as e:
            raise FieldValidationError(FieldError(self, 'invalid', errors=schema._raw_errors))

    def __setattr__(self, k, v):
        if k == '_schema':
            if getattr(self, 'cached'):
                self.cached._schema = v
                for field in self.cached._fields:
                    # NOTE: this could interfere with the _schema if it's purpose changes in the future
                    self.cached._fields[field]._schema = v
        super(Field, self).__setattr__(k, v)


class SelfReference(Field):

    __slots__ = ['exclude', 'cached']

    messages = {'invalid': 'Invalid Schema',
                'invalid_mapping': 'Field is not a valid Schema Mapping type'}

    def new(self, *args, **kwargs):
        self.cached = None
        self.exclude = kwargs.get('exclude', [])
        self.whitelist = kwargs.get('whitelist', [])
        self.tags = kwargs.get('tags', [])

    def _get_schema(self):
        if not self.cached:
            self.cached = self._schema.__class__()
        return self.cached

    def serialize(self, value, **kwargs):
        schema = self.cached or self._get_schema()
        return schema.serialize(value, exclude=self.exclude, whitelist=self.whitelist, tags=self.tags)

    def deserialize(self, value):
        schema = self.cached or self._get_schema()
        return schema.__class__(**value)

    def validate(self, value):
        if not hasattr(value, '__dict__') and (type(value) is not dict or not isinstance(value, dict)):
            raise FieldValidationError(FieldError(self, 'invalid_mapping', errors=schema._raw_errors))
        schema = self.cached or self._get_schema()
        schema._raw_errors = {}
        schema._error_handler.reset()
        try:
            return schema.validate(value, **self._schema._validation_opts)
        except ValidationError as e:
            raise FieldValidationError(FieldError(self, 'invalid', errors=schema._raw_errors))


class Date(Field):

    messages = {'invalid': 'Invalid ISO-8601 Date'}

    def serialize(self, value, **kwargs):
        try:
            value = datetime.datetime(value.year, value.month, value.day)
            return value.isoformat('_').split('_')[0]
        except Exception:
            raise SerializationError

    def deserialize(self, value):
        return value

    def validate(self, value):
        if type(value) is datetime.date:
            return value
        
        if type(value) is datetime.datetime:
            return datetime.date(value.year, value.month, value.day)

        if isinstance(value, datetime.date) or isinstance(value, datetime.datetime):
            return datetime.date(value.year, value.month, value.day)

        try:
            dt = parse_datetime(value)
            if dt:
                return datetime.date(dt.year, dt.month, dt.day)
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

    def serialize(self, value, **kwargs):
        try:
            return value.isoformat()
        except Exception:
            raise SerializationError

    def deserialize(self, value):
        return value

    def validate(self, value):
        if isinstance(value, datetime.date):
            return value
        try:
            dt = parse_datetime(value)
            if dt:
                return dt
            raise FieldValidationError(FieldError(self, 'invalid'))
        except (ValueError, TypeError):
            raise FieldValidationError(FieldError(self, 'invalid'))


class UUID(Field):

    messages = {'invalid': 'Field is not a valid UUID'}

    def serialize(self, value, **kwargs):
        return str(value)

    def deserialize(self, value):
        return value

    def validate(self, value):
        try:
            return uuid.UUID(value)
        except (ValueError, AttributeError, TypeError):
            pass
        if isinstance(value, uuid.UUID):
            return value
        raise FieldValidationError(FieldError(self, 'invalid'))


