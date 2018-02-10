class SchemaException(Exception):

    def __init__(self, message=None):
        self.message = message


class ValidationError(Exception):

    def __init__(self, schema, message=None):
       self.schema = schema

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


class SerializationError(Exception):
    pass
