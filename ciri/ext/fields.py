import uuid

from ciri.exception import FieldValidationError, SerializationError
from ciri.fields import Field, FieldError
from ciri.compat import str_


class UUID(Field):

    messages = {'invalid': 'Field is not a valid UUID'}

    def serialize(self, value):
        return str(value)

    def deserialize(self, value):
        return value

    def validate(self, value):
        try:
            return uuid.UUID(value)
        except (ValueError, AttributeError):
            pass
        if isinstance(value, uuid.UUID):
            return value
        raise FieldValidationError(FieldError(self, 'invalid'))
