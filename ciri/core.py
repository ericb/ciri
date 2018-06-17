import logging
from abc import ABCMeta

from ciri.abstract import (AbstractField, AbstractSchema, SchemaFieldDefault,
                           SchemaFieldMissing, UseSchemaOption)
from ciri.compat import add_metaclass
from ciri.encoder import JSONEncoder
from ciri.exception import SchemaException, SerializationError, ValidationError, FieldValidationError, RegistryError
from ciri.fields import FieldError, Schema as SchemaField
from ciri.registry import schema_registry


logger = logging.getLogger('ciri')


class ErrorHandler(object):
    """
    Default `Schema` Error Handler.
    """

    def __init__(self):
        #: Holds formatted Errors
        self.errors = {}

    def reset(self):
        """Clears the current error context"""
        self.errors = {}

    def add(self, key, field_error):
        """Takes a `FieldError`

        :param key: error key 
        :type key: str

        """
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
        if self.output_missing:  # implies None fields can be output
            self.allow_none = True


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


class AbstractPolySchema(AbstractSchema):
    pass


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
        klass._elements = {}
        klass._subfields = {}
        klass._pending_schemas = {}
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

    @staticmethod
    def prepare_class(cls, name, bases, attrs):
        """ Prepares the class instance for different Schema types. Currently
        this only handles the :class:`PolySchema` type and it's subclasses."""
        clear_poly = False
        meta = False

        # Meta : compose attributes
        if 'Meta' in attrs and getattr(attrs['Meta'], 'compose', None):
            compose = getattr(attrs['Meta'], 'compose')
            base_includes = getattr(attrs, '__schema_include__', [])
            attrs['__schema_include__'] = [s for s in compose] + base_includes

        # Meta : poly_id
        if 'Meta' in attrs and getattr(attrs['Meta'], 'poly_id', None):
            attrs['__poly_id__'] = getattr(attrs['Meta'], 'poly_id') 

        # Meta : options
        if 'Meta' in attrs and getattr(attrs['Meta'], 'options', None):
            attrs['__schema_options__'] = getattr(attrs['Meta'], 'options') 

        # Meta : tags
        if 'Meta' in attrs and getattr(attrs['Meta'], 'tags', None):
            attrs['__field_tags__'] = getattr(attrs['Meta'], 'tags')

        # Meta : Callables
        if '__schema_callables__' not in attrs:
            attrs['__schema_callables__'] = {}
        callables = SchemaCallableObject().callables
        for type_ in callables:
            if 'Meta' in attrs and getattr(attrs['Meta'], type_, None):
                c = getattr(attrs['Meta'], type_)
                if type(c) not in (list, set,):
                    c = [c]
                attrs['__schema_callables__'][type_] = c

        if '__poly_id__' in attrs:
            clear_poly = True

        if clear_poly:
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
                            newattrs[k] = v.__get__(cls, None)
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
                    base.__poly_mapping__ = {}
                    base.__poly_inherit__ = [x if not x.startswith('__poly') else None for x in attrs]
                if '__poly_id__' in attrs:
                    base.__poly_parent__ = base

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
            if k not in ignore_fields and (isinstance(v, AbstractField) or isinstance(v, AbstractSchema)):
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
        for k, v in self._fields.items():
            if isinstance(v, AbstractField):
                if isinstance(v, SchemaField):
                    try:
                        self._fields[k] = v._get_schema()
                    except (AttributeError, RegistryError):
                        self._pending_schemas[k] = v
                    self._subfields[k] = v
                    self._elements[k] = True
                else:
                    if v.required or (v.default is not SchemaFieldDefault):
                        self._elements[k] = True
                    elif v.output_missing is True or (v.output_missing is UseSchemaOption and self._config.output_missing):
                        self._elements[k] = True
                    # update tags
                    for tag in v.tags:
                        if not self._tags.get(tag):
                            self._tags[tag] = []
                        self._tags[tag].append(k)
            elif isinstance(v, AbstractSchema):
                self._subfields[k] = v
                self._elements[k] = True
        self._e = [x for x in self._elements]

    def __init__(self, *args, **kwargs):
        """Metaclass Init - Maps the current Schema to the :class:`ciri.core.PolySchema` parent
        if the Schema has one"""
        poly_id = getattr(self, '__poly_id__', None)
        if poly_id:
            self.__poly_parent__.__poly_mapping__[poly_id] = self


@add_metaclass(ABCSchema)
class Schema(AbstractSchema):

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            if self._fields.get(k):
                setattr(self, k, v)
        self._validation_opts = {}
        self._serialization_opts = {}
        for k in self._fields:
            self._fields[k]._schema = self
        self.config({})
        self.context = {}

    def config(self, cfg):
        if cfg.get('options') is not None:
            self._config = cfg['options']
        self._error_handler = self._config.error_handler()
        self._registry = self._config.registry
        self._encoder = self._config.encoder

    @property
    def errors(self):
        return self._error_handler.errors

    def pre_process(self, data):
        pass

    def _iterate(self, fields, elements, data, validation_opts,
                 parent=None, do_serialize=False, exclude=[],
                 do_deserialize=False, do_validate=False,
                 whitelist=[], tags=[]):
        errors = {}
        valid = {}
        halt_on_error = validation_opts.get('halt_on_error')
        allow_none = self._config.allow_none
        pre_validate = parent._field_callables.pre_validate
        pre_serialize = parent._field_callables.pre_serialize
        pre_deserialize = parent._field_callables.pre_deserialize
        post_validate = parent._field_callables.post_validate
        post_serialize = parent._field_callables.post_serialize
        post_deserialize = parent._field_callables.post_deserialize
        output_missing = self._config.output_missing

        if do_validate:
            parent._raw_errors = {}
            parent._error_handler.reset()

        if hasattr(data, '__dict__'):
            data = vars(data)

        if whitelist:
            elements = whitelist

        for key in elements:
            if key in exclude:
                continue
            str_key = str(key)

            # field value
            klass_value = data.get(key, SchemaFieldMissing)
            missing = (klass_value is SchemaFieldMissing)
            invalid = False

            field = fields[key]

            # if we encounter a schema field, cache it
            if key in parent._pending_schemas:
                field = self._fields[key] = field._get_schema()
                parent._pending_schemas.pop(key)

            if key in parent._subfields:
                if klass_value is None or missing:
                    errors[key] = FieldError(parent._subfields[key], 'invalid')
                    continue
                data_keys = []
                sub = klass_value
                if hasattr(klass_value, '__dict__'):
                    sub = vars(klass_value)
                for k in sub:  # check the subfield elements to iterate
                    if field._fields.get(k):
                        data_keys.append(k)
                key_cache = set(field._e + data_keys)
                suberrors, valid[key] = self._iterate(field._fields, key_cache, klass_value, validation_opts,
                                                      parent=field, do_serialize=do_serialize, do_validate=do_validate,
                                                      do_deserialize=do_deserialize, exclude=parent._subfields[key].exclude,
                                                      whitelist=parent._subfields[key].whitelist)
                klass_value = valid[key]
                if suberrors:
                    errors[key] = FieldError(parent._subfields[key], 'invalid', errors=suberrors)
                continue

            # if the field is missing, set the default value
            if missing and (fields[key].default is not SchemaFieldDefault):
                if callable(fields[key].default):
                    klass_value = fields[key].default(parent, field)
                else:
                    klass_value = fields[key].default
                missing = False

            # if fields are missing and we allow them in the output,
            # set the value to the field missing output value
            if missing and output_missing:
                klass_value = fields[key].missing_output_value
                missing = False

            if do_validate:

                # run pre validation functions
                if pre_validate:
                    for func in pre_validate.get(key, []):
                        try:
                            klass_value = valid[key] = func(klass_value, schema=parent, field=field)
                            missing = (valid[key] is SchemaFieldMissing)
                        except FieldValidationError as field_exc:
                            errors[str_key] = field_exc.error
                            invalid = True
                            break

                if errors and halt_on_error:
                    break

                # if the field is missing, but it's required, set an error.
                # if a value of None is allowed and we do not have a field, skip validation
                # otherwise, validate the value
                if missing and field.required:
                    errors[str_key] = FieldError(fields[key], 'required')
                    invalid = True
                elif missing and field.allow_none is True:
                    pass
                elif (missing or klass_value is None) and field.allow_none is False:
                    errors[key] = FieldError(field, 'invalid')
                elif (missing or klass_value is None) and allow_none is False and field.allow_none is not True:
                    errors[key] = FieldError(field, 'invalid')
                elif allow_none and field.allow_none is UseSchemaOption and (klass_value is None or klass_value is SchemaFieldMissing):
                    pass
                elif field.allow_none is True and klass_value is None:
                    pass
                elif not missing:
                    try:
                        klass_value = valid[key] = field.validate(klass_value)
                    except FieldValidationError as field_exc:
                        errors[str_key] = field_exc.error
                        invalid = True
                    if post_validate:
                        for validator in post_validate.get(key, []):
                            try:
                                klass_value = valid[key] = validator(valid[key], schema=parent, field=field)
                            except FieldValidationError as field_exc:
                                errors[str_key] = field_exc.error
                                invalid = True
                                break

                if errors and halt_on_error:
                    break


            if not invalid and do_serialize:

                # run pre serialization functions
                if pre_serialize:
                    for func in pre_serialize.get(key, []):
                        klass_value = valid[key] = func(klass_value, schema=parent, field=field)
                        missing = (valid[key] is SchemaFieldMissing)

                # determine the field result name (serialized name)
                name = field.name or key

                # if it's allowed, and the field is missing, set the value to None
                if missing and allow_none and field.allow_none is UseSchemaOption:
                    valid[name] = None
                elif missing and field.allow_none:
                    valid[name] = None
                elif klass_value is None and field.allow_none:
                    valid[name] = None
                else:
                    valid[name] = field.serialize(valid.get(key, klass_value))

                    # run post serialization functions
                    if post_serialize:
                        for func in post_serialize.get(key, []):
                            valid[name] = func(klass_value, schema=parent, field=field)

                    # remove old keys if the serializer renames the field
                    if name != key:
                        del valid[key]

            if not invalid and do_deserialize:

                # run pre deserialization functions
                if pre_deserialize:
                    for func in pre_deserialize.get(key, []):
                        klass_value = valid[key] = func(valid.get(key, klass_value), schema=parent, field=field)
                        missing = (valid[key] is SchemaFieldMissing)

                # if it's allowed, and the field is missing, set the value to None
                if missing and allow_none and field.allow_none is UseSchemaOption:
                    klass_value = valid[key] = None
                elif missing and field.allow_none:
                    klass_value = valid[key] = None
                elif klass_value is None and field.allow_none:
                    klass_value = valid[key] = None
                else:
                    klass_value = valid[key] = field.deserialize(valid.get(key, klass_value))
                    # run post deserialization functions
                    if post_deserialize:
                        for func in post_deserialize.get(key, []):
                            klass_value = valid[key] = func(klass_value, schema=parent, field=field)
        for e, err in errors.items():
            parent._raw_errors[e] = err
            parent._error_handler.add(e, err)
        return (errors, valid)

    def validate(self, data=None, halt_on_error=False, key_cache=None, exclude=[], whitelist=[]):
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

        if whitelist:
            key_cache = set(whitelist)

        errors, valid = self._iterate(self._fields, key_cache, data,
                                      self._validation_opts, parent=self,
                                      do_validate=True, exclude=exclude,
                                      whitelist=whitelist)
        if self._config.raise_errors and errors:
            raise ValidationError(self)
        return valid

    def serialize(self, data=None, skip_validation=False, exclude=[],
                  whitelist=[], tags=[], context=None):
        data = data or self
        if hasattr(data, '__dict__'):
            data = vars(data)

        context = context or self.context

        if hasattr(self._schema_callables, 'pre_serialize'):
            for c in getattr(self._schema_callables, 'pre_serialize'):
                data = c(data, schema=self, context=context)

        if tags:
            data_keys = []
            append = data_keys.append
            fields = self._fields
            for k in tags:
                if k in self._tags:
                    for t in self._tags[k]:
                        append(t)
            elements = set(data_keys)
            whitelist = []
        elif not whitelist:
            data_keys = []
            append = data_keys.append
            fields = self._fields
            for k in data:
                if fields.get(k):
                    append(k)
            elements = set(self._e + data_keys)
        else:
            elements = set(whitelist)

        errors, output = self._iterate(self._fields, elements, data, self._validation_opts, parent=self,
                                       do_serialize=True, do_validate=(not skip_validation),
                                       exclude=exclude, whitelist=whitelist, tags=tags)
        if self._config.raise_errors and errors:
            raise ValidationError(self)

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

        errors, output = self._iterate(self._fields, elements, data, self._validation_opts, parent=self,
                                       do_deserialize=True, do_validate=(not skip_validation))

        if self._config.raise_errors and errors:
            raise ValidationError(self)

        return self.__class__(**output)

    def encode(self, data=None, skip_validation=False, skip_serialization=False):
        self._encode_stream = []
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

        errors, output = self._iterate(self._fields, elements, data, self._validation_opts, parent=self,
                                       do_serialize=(not skip_serialization), do_validate=(not skip_validation))

        if self._config.raise_errors and errors:
            raise ValidationError(self)

        return self._encoder.encode(output, self)


    def __eq__(self, other):
        if isinstance(other, AbstractSchema):
            if self.serialize() == other.serialize():
                return True
            return False
        return NotImplemented


class PolySchema(AbstractPolySchema, Schema):

    def __init__(self, *args, **kwargs):
        self.__poly_args__ = args
        self.__poly_kwargs__ = kwargs
        super(PolySchema, self).__init__(*args, **kwargs)

    def deserialize(self, data=None, *args, **kwargs):
        ident_key = self.__poly_on__.name
        data = data or self.__poly_kwargs__ or self
        if hasattr(data, '__dict__'):
            data = vars(data)
        id_ = data.get(ident_key)
        if not id_:
            raise SerializationError
        schema = self.__poly_mapping__.get(id_)(*self.__poly_args__, **self.__poly_kwargs__)
        return schema.deserialize(data, *args, **kwargs)

    def serialize(self, data=None, *args, **kwargs):
        ident_key = self.__poly_on__.name
        data = data or self.__poly_kwargs__ or self
        if hasattr(data, '__dict__'):
            data = vars(data)
        id_ = data.get(ident_key)
        if not id_:
            raise SerializationError
        schema = self.__poly_mapping__.get(id_)(*self.__poly_args__, **self.__poly_kwargs__)
        return schema.serialize(data, *args, **kwargs)

    def encode(self, data=None, *args, **kwargs):
        ident_key = self.__poly_on__.name
        data = data or self.__poly_kwargs__ or self
        if hasattr(data, '__dict__'):
            data = vars(data)
        id_ = data.get(ident_key)
        if not id_:
            raise SerializationError
        schema = self.__poly_mapping__.get(id_)(*self.__poly_args__, **self.__poly_kwargs__)
        return schema.encode(data, *args, **kwargs)

    @classmethod
    def polymorph(cls, *args, **kwargs):
        ident_key = cls.__poly_on__.name
        id_ = kwargs.get(ident_key)
        schema = cls.__poly_mapping__.get(id_)(*args, **kwargs)
        return schema
