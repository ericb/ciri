class SchemaException(Exception):
    pass


class InvalidSchemaException(SchemaException):

    def __init__(self, message='', errors=None, *args, **kwargs):
        super(InvalidSchemaException, self).__init__(message, *args, **kwargs)
        if errors:
            self._errors = errors


class SerializationException(Exception):
    pass
