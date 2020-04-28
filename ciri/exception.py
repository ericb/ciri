class SchemaException(Exception):

    def __init__(self, message=None):
        self.message = message


class ValidationError(Exception):

    def __init__(self, schema, message=None):
       self.schema = schema
       self.message = message

    def __repr__(self):
        return '{}(schema={}, message={})'.format(
            self.__class__.__name__,
            repr(self.schema),
            repr(self.message)
        )

    def __str__(self):
        return '{} {}'.format(self.__repr__(), self.errors)

    @property
    def errors(self):
        return self.schema.errors


class RegistryError(Exception):
    pass


class InvalidSchemaException(SchemaException):

    def __init__(self, message='', errors=None, *args, **kwargs):
        super(InvalidSchemaException, self).__init__(message, *args, **kwargs)
        if errors:
            self._errors = errors


class FieldValidationError(ValidationError):

    def __init__(self, field_error, *args, **kwargs):
        self.error = field_error

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.error))

    def __str__(self):
        return self.__repr__()

class SerializationError(SchemaException):
    pass


class FieldError(object):

    def __init__(self, field_cls, field_msg_key=None, errors=None, *args, **kwargs):
        self.field = field_cls
        self.message_key = field_msg_key
        self.message = kwargs.get('message') or field_cls.message[field_msg_key]
        self.errors = errors

    def __repr__(self):
        return '{}({}, field_msg_key={}, errors={}, message={})'.format(
            self.__class__.__name__,
            repr(self.field),
            repr(self.message_key),
            repr(self.errors),
            repr(self.message)
        )

    def __str__(self):
        return self.__repr__()
