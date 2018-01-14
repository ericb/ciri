from abc import ABCMeta

from ciri.abstract import AbstractField, AbstractBaseSchema, SchemaFieldDefault, SchemaFieldMissing
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


@add_metaclass(AbstractBaseSchema)
class Schema(object):

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            if self._fields.get(k):
                setattr(self, k, kwargs[k])
        self.raw_errors = None
        self.error_handler = kwargs.get('error_handler', ErrorHandler)()
        self.registry = kwargs.get('schema_registry', schema_registry)

    def __setattr__(self, k, v):
        if self._fields.get(k):
            self._elements[k] = True
        super(Schema, self).__setattr__(k, v)

    @property
    def errors(self):
        return self.error_handler.errors

    def pre_process(self, data):
        pass

    def validate(self, data, halt_on_error=False):
        self.raw_errors = {}
        self.error_handler.reset()

        elements = self._elements.copy()
        if hasattr(data, '__dict__'):
            data = vars(data)

        for k, v in data.items():
            if self._fields.get(k):
                elements[k] = True

        for key in elements.keys():
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
                self.raw_errors[str_key] = field_err
                self.error_handler.add(str_key, field_err)
            elif self._fields[key].allow_none and (klass_value == SchemaFieldMissing):
                pass
            else:
                try:
                    self._fields[key].validate(klass_value)
                except FieldValidationError as field_exc:
                    self.raw_errors[str_key] = field_exc.error
                    self.error_handler.add(str_key, field_exc.error)
            if self.errors and halt_on_error:
                break

        if self.errors:
            raise ValidationError()
        return self

    def serialize(self, data=None, skip_validation=False):
        output = {}
        elements = self._elements.copy()
        if data is None:
            data = self

        if hasattr(data, '__dict__'):
            data = vars(data)

        for k in data:
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

            # determine the field result name (serialized name)
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
