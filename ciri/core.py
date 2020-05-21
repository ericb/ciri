import logging
from abc import ABCMeta

from ciri.abstract import (AbstractField,
                           AbstractSchema,
                           AbstractPolySchema,
                           SchemaFieldDefault,
                           SchemaFieldMissing, UseSchemaOption)
from ciri.compat import add_metaclass
from ciri.encoder import JSONEncoder
from ciri.exception import SchemaException, SerializationError, ValidationError, FieldValidationError, \
    RegistryError, FieldError
from ciri.fields import Schema as SchemaField
from ciri.registry import schema_registry


logger = logging.getLogger('ciri')


class ErrorHandler(object):
    """
    Default `Schema` Error Handler.
    """

    def __init__(self):
        #: Holds formatted Errors
        self.errors = {}
        self._raw_errors = {}

    def reset(self):
        """Clears the current error context"""
        self.errors = {}
        self._raw_errors = {}

    def add(self, key, field_error):
        """Takes a `FieldError`

        :param key: error key 
        :type key: str

        """
        self._raw_errors[key] = field_error
        key = str(key)
        self.errors[key] = {'msg': field_error.message}
        if field_error.errors:
            handler = self.__class__()
            for k, v in field_error.errors.items():
                handler.add(k, v)
            self.errors[key]['errors'] = handler.errors


class SchemaOptions(object):
    """
    Holds the schema behavior configuration


    :param allow_none: Allow :class:`None` values
    :param raise_errors: Whether or not to raise exceptions
    :param error_handler: Schema error handling
    :param encoder: Schema encoding handler
    :param registry: Schema registry
    :param output_missing: Include :class:`~ciri.core.SchemaFieldMissing` values in serialization output

    :type allow_none: bool
    :type raise_errors: bool
    :type error_handler: :class:`~ciri.core.ErrorHandler`
    :type encoder: :class:`~ciri.encoder.SchemaEncoder`
    :type registry: :class:`~ciri.registry.SchemaRegistry`
    :type output_missing: bool
    """

    def __init__(self, *args, **kwargs):
        defaults = {
            'allow_none': False,
            'raise_errors': True,
            'error_handler': ErrorHandler,
            'encoder': JSONEncoder(),
            'registry': schema_registry,
            'output_missing': False
        }
        options = dict((k, v) if k in defaults else ('_unknown', 1) for (k,v) in kwargs.items())
        options.pop('_unknown', None)
        defaults.update(options)
        for k, v in defaults.items():
            setattr(self, k, v)


DEFAULT_SCHEMA_OPTIONS = SchemaOptions()


class SchemaCallableObject(object):

    def __init__(self, *args, **kwargs):
        self.callables = ['pre_validate', 'pre_serialize', 'pre_deserialize',
                          'post_validate', 'post_serialize', 'post_deserialize']
        for c in self.callables:
            setattr(self, c, kwargs.get(c, []))

    def find(self, schema):
        lookup = getattr(schema, '__schema_callables__', None)
        if not lookup:
            setattr(schema, '__schema_callables__', {})
            lookup = schema.__schema_callables__
        for c in self.callables:
            schema_callable = schema.__schema_callables__.get(c)
            if schema_callable:
                updated_callables = []
                for item in schema_callable:
                    if callable(item):
                        updated_callables.append(item)
                    else:
                        method = getattr(schema, item, None)
                        if callable(method):
                            updated_callables.append(method.__get__(schema, None))
                setattr(self, c, updated_callables)


class FieldCallableObject(object):

    def __init__(self, *args, **kwargs):
        self.callables = ['pre_validate', 'pre_serialize', 'pre_deserialize',
                          'post_validate', 'post_serialize', 'post_deserialize']
        for c in self.callables:
            setattr(self, c, kwargs.get(c, {}))

    def find(self, schema):
        for key, field in schema._fields.items():
            if isinstance(field, Schema):
                continue  # schemas will handle their own
            for c in self.callables:
                field_callable = getattr(field, c, None)
                if field_callable:
                    updated_callables = []
                    for item in field_callable:
                        if callable(item):
                            updated_callables.append(item)
                        else:
                            method = getattr(schema, item, None)
                            if callable(method):
                                updated_callables.append(method.__get__(schema, None))
                    getattr(self, c)[key] = updated_callables


class ABCSchema(ABCMeta):
    """
    Schema Metaclass

    Looks for :class:`ciri.fields.Field` attributes and handles the schema
    magic methods.
    """

    def __new__(cls, name, bases, attrs):
        cls, name, bases, attrs = cls.prepare_class(cls, name, bases, attrs)
        klass = ABCMeta.__new__(cls, name, bases, dict(attrs))
        klass._fields = {}
        klass._tags = {}
        klass._subschemas = {}
        klass._pending_schemas = {}
        klass._load_keys = {}
        klass._schema_callables = SchemaCallableObject()
        klass._field_callables = FieldCallableObject()
        klass._config = DEFAULT_SCHEMA_OPTIONS
        klass.handle_bases(bases)
        klass.handle_poly(cls, name, bases, attrs)
        klass.handle_config()
        klass.handle_tags()
        klass.find_fields()
        klass.process_fields()
        klass._schema_callables.find(klass)
        klass._field_callables.find(klass)
        return klass

    def __init__(self, *args, **kwargs):
        """Metaclass Init - Maps the current Schema to the :class:`ciri.core.PolySchema` parent
        if the Schema has one"""
        poly_id = getattr(self, '__poly_id__', None)
        if poly_id:
            self.__poly_parent__.__poly_mapping__[poly_id] = self
        self._og_schema = self

    @staticmethod
    def prepare_class(cls, name, bases, attrs):
        """ Prepares the class instance for different Schema types. Currently
        this only handles the :class:`PolySchema` type and it's subclasses."""

        if 'Meta' in attrs:
            # Meta : compose attributes
            if getattr(attrs['Meta'], 'compose', None):
                compose = getattr(attrs['Meta'], 'compose')
                base_includes = getattr(attrs, '__schema_include__', [])
                attrs['__schema_include__'] = [s for s in compose] + base_includes

            # Meta : poly_id
            if getattr(attrs['Meta'], 'poly_id', None):
                attrs['__poly_id__'] = getattr(attrs['Meta'], 'poly_id') 

            # Meta : options
            if getattr(attrs['Meta'], 'options', None):
                attrs['__schema_options__'] = getattr(attrs['Meta'], 'options') 

            # Meta : tags
            if getattr(attrs['Meta'], 'tags', None):
                attrs['__field_tags__'] = getattr(attrs['Meta'], 'tags')

            # Meta : Callables
            attrs['__schema_callables__'] = attrs.get('__schema_callables__') or {}
            callables = SchemaCallableObject().callables
            for type_ in callables:
                if getattr(attrs['Meta'], type_, None):
                    c = getattr(attrs['Meta'], type_)
                    if type(c) not in (list, set,):
                        c = [c]
                    attrs['__schema_callables__'][type_] = c

        if '__poly_id__' in attrs:
            updated_bases = []
            for base in bases:
                if issubclass(base, AbstractPolySchema):
                    props = []
                    for x in base.__poly_inherit__:
                        if x:
                            props.append(x)
                    newattrs = dict((x, getattr(base, x, None)) for x in props)
                    for k, v in newattrs.items():
                        if callable(v):
                            if type(v) is not type:
                                try:
                                    from types import TypeType, ClassType
                                    if type(v) not in (TypeType, ClassType):
                                        newattrs[k] = v.__get__(cls, None)
                                    else:
                                        newattrs[k] = v
                                except Exception:
                                    newattrs[k] = v.__get__(cls, None)
                            else:
                                newattrs[k] = v
                    newattrs.update(attrs)
                    attrs = newattrs
                    attrs['__poly_parent__'] = base
                    attrs.update(base._fields)
                    continue
                updated_bases.append(base)
            updated_bases.append(Schema)
            bases = tuple(updated_bases)

        return cls, name, bases, attrs

    def handle_bases(self, bases):
        """Handles the Schema inheritance, specifically bringing in the inherited
        field attributes"""
        for base in bases:
            if hasattr(base, '_fields'):
                self._fields.update(base._fields)

    def handle_poly(self, cls, name, bases, attrs):
        """Handles magic methods (e.g. `__poly_on__`) of :class:`~ciri.core.PolySchema`
        definitions."""
        for base in bases:
            if issubclass(base, AbstractPolySchema):
                if '__poly_on__' in attrs:
                    self.__poly_mapping__ = {}
                    self.__poly_inherit__ = [x if not x.startswith('__poly') else None for x in attrs]

    def handle_config(self):
        """Handles the schema options magic method"""
        if hasattr(self, '__schema_options__'):
            self._config = getattr(self, '__schema_options__')

    def handle_tags(self):
        """Handles the field tags magic method"""
        if hasattr(self, '__field_tags__'):
            self._tags = getattr(self, '__field_tags__')

    def find_fields(self):
        """Find the :class:`~ciri.fields.Field` attributes and store them in the
        schemas `_fields` attribute."""
        items = dict((k,v) for k,v in vars(self).items())
        includes = getattr(self, '__schema_include__', None)
        inc = {}
        if includes:
            for inc_item in includes:
                if isinstance(inc_item, ABCSchema):
                    inc.update(inc_item._fields)
                else:
                    inc.update(inc_item)
        inc.update(items)
        ignore_fields = ['__poly_on__']
        for k, v in inc.items():
            if k not in ignore_fields and isinstance(v, AbstractField):
                if not v.name:
                    v.name = k
                self._fields[k] = v
                if k in items:
                    delattr(self, k)
            elif k in self._fields:
                self._fields.pop(k)  # a subclass has overriden the field

    def process_fields(self):
        """Performs field processing. Handles:

          * Tracking required fields or fields that should always be checked
          * Tracking nested fields (aka, sub schemas)
          * Tracking deferred schema fields
          * Converting :class:`ciri.fields.Schema` fields to Schemas
        """
        self._check_elements = []
        for k, v in self._fields.items():
            if isinstance(v, AbstractField):
                if isinstance(v, SchemaField):
                    self._check_elements.append(k)
                    self._pending_schemas[k] = v
                elif v.required or (v.default is not SchemaFieldDefault):
                    self._check_elements.append(k)
                elif v.output_missing is True or (v.output_missing is UseSchemaOption and self._config.output_missing):
                    self._check_elements.append(k)
                if v.load:
                    self._load_keys.setdefault(v.load, []).append(k)
                # update tags
                for tag in v.tags:
                    if not self._tags.get(tag):
                        self._tags[tag] = []
                    self._tags[tag].append(k)
            elif isinstance(v, AbstractSchema):
                self._subschemas[k] = v


@add_metaclass(ABCSchema)
class Schema(AbstractSchema):

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            if self._fields.get(k):
                setattr(self, k, v)
                if isinstance(self._fields[k], SchemaField) and isinstance(v, AbstractSchema):
                    self._fields[k].cached = v
        for k in self._fields:
            if k in self._pending_schemas:
                try:
                    self._subschemas[k] = self._fields[k]._get_schema()
                    self._pending_schemas.pop(k)
                except (AttributeError, RegistryError):
                    pass
            self._fields[k]._schema = self
            self._fields[k]._og_schema = self._og_schema
        self.config({})
        self.context = {}
        self.halt_on_error = False

    def __eq__(self, other):
        if isinstance(other, AbstractSchema):
            if self.serialize() == other.serialize():
                return True
            return False
        return NotImplemented

    def config(self, cfg):
        if cfg.get('options') is not None:
            self._config = cfg['options']
        self._error_handler = self._config.error_handler()
        self._registry = self._config.registry
        self._encoder = self._config.encoder

    @property
    def errors(self):
        return self._error_handler.errors

    @property
    def _raw_errors(self):
        return self._error_handler._raw_errors

    def _validate_element(self, field, key, klass_value, output_missing, allow_none):
        # run pre validation functions
        pre_validate = self._field_callables.pre_validate
        if pre_validate:
            for func in pre_validate.get(key, []):
                try:
                    klass_value = func(klass_value, schema=self, field=field)
                except FieldValidationError as field_exc:
                    self._error_handler.add(key, field_exc.error)
                    break

        if self.errors and self.halt_on_error:
            return klass_value

        missing = (klass_value is SchemaFieldMissing)

        # if the field is missing, but it's required, set an error.
        # if a value of None is allowed and we do not have a field, skip validation
        # otherwise, validate the value
        if missing:
            if field.required:
                self._error_handler.add(key, FieldError(field, 'required'))
            elif not allow_none:
                self._error_handler.add(key, FieldError(field, 'required' if field.required else 'invalid'))
        elif klass_value is None:
            if not output_missing and not allow_none:
                self._error_handler.add(key, FieldError(field, 'required' if field.required else 'invalid'))
        else:
            try:
                klass_value = field.validate(klass_value)
            except FieldValidationError as field_exc:
                self._error_handler.add(key, field_exc.error)

        # run post validation functions
        post_validate = self._field_callables.post_validate
        if post_validate:
            for validator in post_validate.get(key, []):
                try:
                    klass_value = validator(klass_value, schema=self, field=field)
                except FieldValidationError as field_exc:
                    self._error_handler.add(key, field_exc.error)
                    break

        return klass_value

    def _serialize_element(self, field, key, klass_value):
        # run pre serialization functions
        pre_serialize = self._field_callables.pre_serialize
        if pre_serialize:
            for func in pre_serialize.get(key, []):
                klass_value = func(klass_value, schema=self, field=field)

        missing = (klass_value is SchemaFieldMissing)

        # if it's allowed, and the field is missing, set the value to None
        # otherwise, run the primary function
        if missing or klass_value is None:
            klass_value = None
        else:
            klass_value = field.serialize(klass_value)

        # run post serialization functions
        post_serialize = self._field_callables.post_serialize
        if post_serialize:
            for func in post_serialize.get(key, []):
                klass_value = func(klass_value, schema=self, field=field)

        return klass_value

    def _deserialize_element(self, field, key, klass_value):
        # run pre deserialization functions
        pre_deserialize = self._field_callables.pre_deserialize
        if pre_deserialize:
            for func in pre_deserialize.get(key, []):
                klass_value = func(klass_value, schema=self, field=field)

        missing = (klass_value is SchemaFieldMissing)

        # if it's allowed, and the field is missing, set the value to None
        # otherwise, run the primary function
        if missing or klass_value is None:
            klass_value = None
        else:
            klass_value = field.deserialize(klass_value)

        # run post deserialization functions
        post_deserialize = self._field_callables.post_deserialize
        if post_deserialize:
            for func in post_deserialize.get(key, []):
                klass_value = func(klass_value, schema=self, field=field)

        return klass_value

    def _iterate(
        self,
        data,
        exclude=None,
        whitelist=None,
        tags=None,
        do_validate=False,
        do_deserialize=False,
        do_serialize=False
    ):
        output_missing = self._config.output_missing
        allow_none = self._config.allow_none

        if do_validate:
            self._error_handler.reset()

        # get elements
        if tags:
            data_keys = []
            for tag in tags:
                data_keys.extend(self._tags.get(tag, []))
            elements = set(data_keys)
        elif whitelist:
            elements = set(whitelist)
        else:
            data_keys = []
            for k in data:
                if self._fields.get(k):
                    data_keys.append(k)
                elif self._load_keys.get(k):
                    data_keys.extend(self._load_keys[k])
            elements = set(self._check_elements + data_keys)

        exclude = set(exclude) if exclude else set()

        output = {}
        for key in elements:
            if key in exclude:
                continue

            field = self._fields[key]

            if field.output_missing is not UseSchemaOption:
                output_missing = field.output_missing
            if field.allow_none is not UseSchemaOption:
                allow_none = field.allow_none

            # field value
            if do_serialize:
                klass_value = data.get(key, SchemaFieldMissing)
            elif do_deserialize or do_validate:
                load_key = getattr(field, 'load', None) or key
                klass_value = data.get(load_key, SchemaFieldMissing)
            if do_validate and klass_value is SchemaFieldMissing:
                klass_value = data.get(key, SchemaFieldMissing)

            missing = (klass_value is SchemaFieldMissing)

            # if we encounter a schema field, cache it
            if key in self._pending_schemas:
                self._subschemas[key] = field._get_schema()
                self._pending_schemas.pop(key)

            if key in self._subschemas and klass_value is not None and not missing:
                subschema = self._subschemas[key]  # reference the subschema
                if isinstance(subschema, AbstractPolySchema):
                    try:
                        polykey = subschema.getpolyname()
                        if hasattr(klass_value, '__dict__'):
                            klass_value = vars(klass_value)
                        subschema.getpoly(klass_value[polykey])()
                    except Exception:
                        self._error_handler.add(key, FieldError(field, 'invalid_polykey'))
                        continue

            # if the field is missing and we do not output_missing skip it
            if not field.required and missing and not output_missing:
                continue

            if output_missing:
                # if the field is missing, set the default value
                if (missing or klass_value is None) and (field.default is not SchemaFieldDefault):
                    if callable(field.default):
                        klass_value = field.default(self, field)
                    else:
                        klass_value = field.default
                    missing = False

                # if fields are not required, but missing and
                # we allow them in the output, set the value to
                # the field missing output value
                if not field.required and missing:
                    klass_value = field.missing_output_value


            if do_validate:
                # sets klass_value prior to serialization/deserialization
                output[key] = klass_value = self._validate_element(field, key, klass_value, output_missing, allow_none)
                if self.errors and self.halt_on_error:
                    break
                elif self.errors:
                    continue

            if do_serialize:
                # determine the field result name (serialized name)
                output_key = field.name or key

                output[output_key] = self._serialize_element(field, output_key, klass_value)

                # remove old keys if the serializer renames the field
                if output_key != key:
                    del output[key]

            if do_deserialize:
                output[key] = self._deserialize_element(field, key, klass_value)

        return output

    def validate(self, data=None, halt_on_error=False, exclude=None, 
                 whitelist=None, tags=None, context=None):
        data = data or self
        if hasattr(data, '__dict__'):
            data = vars(data)

        self.halt_on_error = halt_on_error

        if hasattr(self._schema_callables, 'pre_validate'):
            context = context or self.context
            for c in getattr(self._schema_callables, 'pre_validate'):
                data = c(data, schema=self, context=context)

        output = self._iterate(
            data,
            exclude=exclude,
            whitelist=whitelist,
            tags=tags,
            do_validate=True
        )

        if hasattr(self._schema_callables, 'post_validate'):
            context = context or self.context
            for c in getattr(self._schema_callables, 'post_validate'):
                valid = c(valid, schema=self, context=context)

        if self._config.raise_errors and self.errors:
            raise ValidationError(self)
        return output

    def serialize(self, data=None, skip_validation=False, exclude=None,
                  whitelist=None, tags=None, context=None):
        data = data or self
        if hasattr(data, '__dict__'):
            data = vars(data)

        if hasattr(self._schema_callables, 'pre_serialize'):
            context = context or self.context
            for c in getattr(self._schema_callables, 'pre_serialize'):
                data = c(data, schema=self, context=context)

        output = self._iterate(
            data,
            exclude=exclude,
            whitelist=whitelist,
            tags=tags,
            do_validate=(not skip_validation),
            do_serialize=True
        )

        if hasattr(self._schema_callables, 'post_serialize'):
            context = context or self.context
            for c in getattr(self._schema_callables, 'post_serialize'):
                output = c(output, schema=self, context=context)

        if self._config.raise_errors and self.errors:
            raise ValidationError(self)
        return output

    def deserialize(self, data=None, skip_validation=False, exclude=None,
                    whitelist=None, tags=None, context=None):
        data = data or self
        if hasattr(data, '__dict__'):
            data = vars(data)

        if hasattr(self._schema_callables, 'pre_deserialize'):
            context = context or self.context
            for c in getattr(self._schema_callables, 'pre_deserialize'):
                data = c(data, schema=self, context=context)

        output = self._iterate(
            data,
            exclude=exclude,
            whitelist=whitelist,
            tags=tags,
            do_validate=(not skip_validation),
            do_deserialize=True
        )

        if hasattr(self._schema_callables, 'post_deserialize'):
            context = context or self.context
            for c in getattr(self._schema_callables, 'post_deserialize'):
                output = c(output, schema=self, context=context)

        if self._config.raise_errors and self.errors:
            raise ValidationError(self)
        return self.__class__(**output)

    def encode(self, data=None, skip_validation=False, skip_serialization=False,
               exclude=[], whitelist=[], tags=[], context=None):
        self._encode_stream = []
        data = data or self
        if hasattr(data, '__dict__'):
            data = vars(data)

        output = self._iterate(
            data,
            exclude=exclude,
            whitelist=whitelist,
            tags=tags,
            do_validate=(not skip_validation),
            do_serialize=(not skip_serialization)
        )

        if self._config.raise_errors and self.errors:
            raise ValidationError(self)
        return self._encoder.encode(output, self)


class PolySchema(AbstractPolySchema, Schema):

    def __init__(self, *args, **kwargs):
        self.__poly_args__ = args
        self.__poly_kwargs__ = kwargs
        super(PolySchema, self).__init__(*args, **kwargs)

    def deserialize(self, data=None, *args, **kwargs):
        ident_key = self.__poly_on__.name
        if self.__poly_on__.load:
            ident_key = self.__poly_on__.load
        data = data or self.__poly_kwargs__ or self
        if hasattr(data, '__dict__'):
            data = vars(data)
        id_ = data.get(ident_key)
        if not id_:
            raise SerializationError(
                "[{}] Failed to find polymorphic key '{}' in input data".format(
                    self.__class__.__name__,
                    ident_key
                )
            )
        if not self.__poly_mapping__.get(id_):
            raise SerializationError(
                "[{}] Failed to find polymorphic identifier '{}' in mapping {}".format(
                    self.__class__.__name__,
                    id_,
                    self.__poly_mapping__
                )
            )
        schema = self.__poly_mapping__.get(id_)(*self.__poly_args__, **self.__poly_kwargs__)
        return schema.deserialize(data, *args, **kwargs)

    def serialize(self, data=None, *args, **kwargs):
        ident_key = self.__poly_on__.name
        data = data or self.__poly_kwargs__ or self
        if hasattr(data, '__dict__'):
            data = vars(data)
        id_ = data.get(ident_key)
        if not id_:
            raise SerializationError(
                "[{}] Failed to find polymorphic key '{}' in input data".format(
                    self.__class__.__name__,
                    ident_key
                )
            )
        if not self.__poly_mapping__.get(id_):
            raise SerializationError(
                "[{}] Failed to find polymorphic identifier '{}' in mapping {}".format(
                    self.__class__.__name__,
                    id_,
                    self.__poly_mapping__
                )
            )
        schema = self.__poly_mapping__.get(id_)(*self.__poly_args__, **self.__poly_kwargs__)
        return schema.serialize(data, *args, **kwargs)

    def validate(self, data=None, *args, **kwargs):
        ident_key = self.__poly_on__.name
        data = data or self.__poly_kwargs__ or self
        if hasattr(data, '__dict__'):
            data = vars(data)
        id_ = data.get(ident_key)
        if not id_:
            raise SerializationError(
                "[{}] Failed to find polymorphic key '{}' in input data".format(
                    self.__class__.__name__,
                    ident_key
                )
            )
        if not self.__poly_mapping__.get(id_):
            raise SerializationError(
                "[{}] Failed to find polymorphic identifier '{}' in mapping {}".format(
                    self.__class__.__name__,
                    id_,
                    self.__poly_mapping__
                )
            )
        schema = self.__poly_mapping__.get(id_)(*self.__poly_args__, **self.__poly_kwargs__)
        return schema.validate(data, *args, **kwargs)

    def encode(self, data=None, *args, **kwargs):
        ident_key = self.__poly_on__.name
        data = data or self.__poly_kwargs__ or self
        if hasattr(data, '__dict__'):
            data = vars(data)
        id_ = data.get(ident_key)
        if not id_:
            raise SerializationError(
                "[{}] Failed to find polymorphic key '{}' in input data".format(
                    self.__class__.__name__,
                    ident_key
                )
            )
        if not self.__poly_mapping__.get(id_):
            raise SerializationError(
                "[{}] Failed to find polymorphic identifier '{}' in mapping {}".format(
                    self.__class__.__name__,
                    id_,
                    self.__poly_mapping__
                )
            )
        schema = self.__poly_mapping__.get(id_)(*self.__poly_args__, **self.__poly_kwargs__)
        return schema.encode(data, *args, **kwargs)

    @classmethod
    def getpolyname(cls):
        return cls.__poly_on__.name

    @classmethod
    def getpoly(cls, key):
        return cls.__poly_mapping__.get(key, None)

    @classmethod
    def polymorph(cls, *args, **kwargs):
        ident_key = cls.__poly_on__.name
        id_ = kwargs.get(ident_key)
        if not id_:
            raise SerializationError(
                "[{}] Failed to find polymorphic key '{}' in input data".format(
                    cls.__name__,
                    ident_key
                )
            )
        schema = cls.getpoly(id_)
        if not schema:
            raise SerializationError(
                "[{}] Failed to find polymorphic identifier '{}' in mapping {}".format(
                    cls.__name__,
                    id_,
                    cls.__poly_mapping__
                )
            )
        return schema(*args, **kwargs)
