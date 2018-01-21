import logging
from abc import ABCMeta

from ciri.abstract import AbstractField, AbstractSchema, SchemaFieldDefault, SchemaFieldMissing, UseSchemaOption
from ciri.compat import add_metaclass
from ciri.exception import SchemaException, SerializationError, ValidationError, FieldValidationError
from ciri.fields import FieldError, Schema as SchemaField
from ciri.registry import schema_registry


logger = logging.getLogger('ciri')


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
        klass._subfields = {}
        klass._pending_schemas = {}
        if not hasattr(klass, '_config'):
            klass._config = DEFAULT_SCHEMA_OPTIONS
        for base in bases:
            if getattr(base, '_fields', None):
                for bk, bv in base._fields.items():
                    if isinstance(bv, SchemaField):
                        try:
                            klass._fields[bk] = bv._get_schema()
                        except AttributeError:
                            klass._pending_schemas[bk] = bv
                            klass._fields[bk] = bv
                        klass._subfields[bk] = bv
                        klass._elements[bk] = True
                    elif isinstance(bv, Schema):
                        klass._fields[bk] = bv
                        klass._subfields[bk] = SchemaField(bv)
                        klass._elements[bk] = True
                    else:
                        klass._fields[bk] = bv
                        if bv.required or bv.allow_none or (bv.default is not SchemaFieldDefault):
                            klass._elements[bk] = True
        for k, v in attrs.items():
            if isinstance(v, AbstractField):
                if isinstance(v, SchemaField):
                    try:
                        klass._fields[k] = v._get_schema()
                    except AttributeError:
                        klass._pending_schemas[k] = v
                        klass._fields[k] = v
                    klass._subfields[k] = v
                    klass._elements[k] = True
                else:
                    klass._fields[k] = v
                    if v.required or v.allow_none or (v.default is not SchemaFieldDefault):
                        klass._elements[k] = True
                delattr(klass, k)
            elif isinstance(v, AbstractSchema):
                klass._fields[k] = v
                klass._subfields[k] = v
                klass._elements[k] = True
                delattr(klass, k)
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

    def _iterate(self, op, fields, elements, data, validation_opts, parent=None):
        errors = {}
        valid = {}
        halt_on_error = validation_opts.get('halt_on_error')
        allow_none = self._config.allow_none

        if not isinstance(data, dict):
            data = vars(data)

        for key in elements:
            str_key = str(key)

            # field value
            klass_value = data.get(key, SchemaFieldMissing)
            missing = (klass_value == SchemaFieldMissing)
            invalid = False

            field = fields[key]
            
            # if we encounter a schema field, cache it
            if key in parent._pending_schemas:
                field = self._fields[key] = field._get_schema()
                parent._pending_schemas.pop(key)

            if key in parent._subfields:
                data_keys = []
                for k in data:
                    if field._fields.get(k):
                        data_keys.append(k)
                key_cache = set(field._e + data_keys)
                suberrors, valid[key] = self._iterate(op, field._fields, key_cache, klass_value, validation_opts, parent=field)
                if suberrors:
                    errors[key] = FieldError(parent._subfields[key], 'invalid', errors=suberrors)
                continue

            # if the field is missing, set the default value
            if missing and (fields[key].default != SchemaFieldDefault):
                klass_value = fields[key].default
                missing = False

            if op == 'validate_and_serialize' or op == 'validate_and_deserialize' or op == 'validate':
                self._raw_errors = {}
                self._error_handler.reset()

                # if the field is missing, but it's required, set an error.
                # if a value of None is allowed and we do not have a field, skip validation
                # otherwise, validate the value
                if missing and fields[key].required:
                    errors[str_key] = FieldError(fields[key], 'required')
                    invalid = True
                elif missing and field.allow_none:
                    pass
                else:
                    try:
                        valid[key] = field.validate(klass_value)
                    except FieldValidationError as field_exc:
                        errors[str_key] = field_exc.error
                        invalid = True
                if errors and halt_on_error:
                    break
            
            if not invalid and (op == 'validate_and_serialize' or op == 'serialize'):
                # determine the field result name (serialized name)
                name = field.name or key

                # if it's allowed, and the field is missing, set the value to None
                if missing and allow_none and field.allow_none == UseSchemaOption:
                    valid[name] = None
                elif missing and field.allow_none:
                    valid[name] = None
                elif klass_value is None and field.allow_none:
                    valid[name] = None
                else:
                    valid[name] = field.serialize(valid.get(key, klass_value))

            if not invalid and (op == 'validate_and_deserialize' or op == 'deserialize'):
                # if it's allowed, and the field is missing, set the value to None
                if missing and allow_none and field.allow_none == UseSchemaOption:
                    valid[key] = None
                elif missing and field.allow_none:
                    valid[key] = None
                elif klass_value is None and field.allow_none:
                    valid[key] = None
                else:
                    valid[key] = field.deserialize(valid.get(key, klass_value))
        for e, err in errors.items():
            self._raw_errors[e] = err 
            self._error_handler.add(e, err)
        return (errors, valid)

    def validate(self, data=None, halt_on_error=False, key_cache=None):
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

        errors, valid = self._iterate('validate', self._fields, key_cache, data, self._validation_opts, parent=self)
        if errors:
            raise ValidationError()
        return valid

    def serialize(self, data=None, skip_validation=False):
        data = data or self
        if hasattr(data, '__dict__'):
            data = vars(data)

        data_keys = []
        append = data_keys.append
        fields = self._fields
        for k in data:
            if fields.get(k):
                append(k)

        elements = set(self._e + data_keys)

        op = 'validate_and_serialize' 
        if skip_validation:
            op = 'serialize'
        errors, output = self._iterate(op, self._fields, elements, data, self._validation_opts, parent=self)
        if errors:
            raise ValidationError()

        return output

    def deserialize(self, data=None, skip_validation=False):
        data = data or self
        if hasattr(data, '__dict__'):
            data = vars(data)

        data_keys = []
        append = data_keys.append
        fields = self._fields
        for k in data:
            if fields.get(k):
                append(k)

        elements = set(self._e + data_keys)

        op = 'validate_and_deserialize' 
        if skip_validation:
            op = 'deserialize'
        errors, output = self._iterate(op, self._fields, elements, data, self._validation_opts, parent=self)
        if errors:
            raise ValidationError()

        return self.__class__(**output)


    def __eq__(self, other):
        if isinstance(other, AbstractSchema):
            if self.serialize() == other.serialize():
                return True
            return False
        return super(Schema, self).__eq__(other)
