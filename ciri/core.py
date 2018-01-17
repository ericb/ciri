from abc import ABCMeta

from ciri.abstract import AbstractField, AbstractSchema, SchemaFieldDefault, SchemaFieldMissing, UseSchemaOption
from ciri.compat import add_metaclass
from ciri.exception import SchemaException, SerializationException, ValidationError, FieldValidationError
from ciri.fields import FieldError
from ciri.registry import schema_registry


class ErrorHandler(object):

    def __init__(self, errors=None):
        self.errors = {}

    def reset(self):
        self.errors = {}

    def add(self, key, field_error):
        key = str(key)
        self.errors[key] = {'msg': field_error.message}
        if field_error.errors:
            handler = self.__class__()
            for k, v in field_error.errors.items():
                handler.add(k, v)
            self.errors[key]['errors'] = handler.errors


class SchemaOptions(object):

    def __init__(self, *args, **kwargs):
        defaults = {
            'allow_none': False,
            'error_handler': ErrorHandler,
            'schema_registry': schema_registry
        }
        options = dict((k, v) if k in defaults else ('_unknown', 1) for (k,v) in kwargs.items())
        options.pop('_unknown', None)
        defaults.update(options)
        for k, v in defaults.items():
            setattr(self, k, v)


DEFAULT_SCHEMA_OPTIONS = SchemaOptions()


class AbstractBaseSchema(ABCMeta):

    def __new__(cls, name, bases, attrs):
        klass = ABCMeta.__new__(cls, name, bases, dict(attrs))
        klass._elements = {}
        klass._fields = {}
        if not hasattr(klass, '_config'):
            klass._config = DEFAULT_SCHEMA_OPTIONS
        for base in bases:
            if getattr(base, '_fields', None):
                for bk, bv in base._fields.items():
                   klass._fields[bk] = bv
                if bv.required or bv.allow_none or (bv.default is not SchemaFieldDefault):
                    klass._elements[bk] = True
        for k, v in attrs.items():
            if isinstance(v, AbstractField):
                klass._fields[k] = v
                delattr(klass, k)
                if v.required or v.allow_none or (v.default is not SchemaFieldDefault):
                    klass._elements[k] = True
            else:
                setattr(klass, k, v)
        klass._e = [x for x in klass._elements]
        return klass


@add_metaclass(AbstractBaseSchema)
class Schema(AbstractSchema):

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            if self._fields.get(k):
                setattr(self, k, v)
        if kwargs.get('schema_options') is not None:
            self._config = kwargs['schema_options']
        self._error_handler = kwargs.get('error_handler', self._config.error_handler)()
        self._registry = kwargs.get('schema_registry', self._config.schema_registry)
        self._validation_opts = {}
        self._serialization_opts = {}
        for k in self._fields:
            self._fields[k]._schema = self

    @property
    def errors(self):
        return self._error_handler.errors

    def pre_process(self, data):
        pass

    def validate(self, data=None, halt_on_error=False, key_cache=None):
        self._raw_errors = {}
        self._error_handler.reset()
        data = data or self

        if hasattr(data, '__dict__'):
            data = vars(data)

        self._validation_opts = {
            'halt_on_error': halt_on_error
        }

        if not key_cache:
            data_keys = []
            for k in data:
                if self._fields.get(k):
                    data_keys.append(k)
            key_cache = set(self._e + data_keys)

        for key in key_cache:
            str_key = str(key)

            # field value
            klass_value = data.get(key, SchemaFieldMissing)

            # if the field is missing, set the default value
            if (klass_value == SchemaFieldMissing) and (self._fields[key].default is not SchemaFieldDefault):
                klass_value = self._fields[key].default

            # if the field is missing, but it's required, set an error.
            # if a value of None is allowed and we do not have a field, skip validation
            # otherwise, validate the value
            if self._fields[key].required and (klass_value == SchemaFieldMissing):
                field_err = FieldError(self._fields[key], 'required')
                self._raw_errors[str_key] = field_err
                self._error_handler.add(str_key, field_err)
            elif self._fields[key].allow_none and (klass_value == SchemaFieldMissing):
                continue
            else:
                try:
                    self._fields[key].validate(klass_value)
                except FieldValidationError as field_exc:
                    self._raw_errors[str_key] = field_exc.error
                    self._error_handler.add(str_key, field_exc.error)
            if self.errors and halt_on_error:
                break

        if self.errors:
            raise ValidationError()
        return self

    def serialize(self, data=None, skip_validation=False):
        output = {}
        data = data or self

        if hasattr(data, '__dict__'):
            data = vars(data)

        data_keys = []
        for k in data:
            if self._fields.get(k):
                data_keys.append(k)

        elements = set(self._e + data_keys)

        if not skip_validation:
            self.validate(data, key_cache=elements)
            if self.errors:
                raise SerializationException

        for key in elements:
            # field value
            klass_value = data.get(key, SchemaFieldMissing)

            # if the field is missing, set the default value
            if (klass_value == SchemaFieldMissing) and (self._fields[key].default is not SchemaFieldDefault):
                klass_value = self._fields[key].default

            # determine the field result name (serialized name)
            name = self._fields[key].name
            if name is None:
                name = key

            # if it's allowed, and the field is missing, set the value to None
            if self._config.allow_none and self._fields[key].allow_none == UseSchemaOption and (klass_value == SchemaFieldMissing):
                output[name] = None
            elif self._fields[key].allow_none and (klass_value == SchemaFieldMissing):
                output[name] = None
            else:
                # if we have something to work with, try and serialize it
                value = self._fields[key].serialize(klass_value)
                if klass_value != SchemaFieldMissing:
                    output[name] = value
        return output
