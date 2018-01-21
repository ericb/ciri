import uuid

from ciri.exception import FieldValidationError, SerializationError
from ciri.fields import Field, FieldError


class UUID(Field):

    messages = {'invalid': 'Field is not a valid UUID'}

    def serialize(self, value):
        return str(value)

    def deserialize(self, value):
        return value

    def validate(self, value):
        if isinstance(value, uuid.UUID):
            return value
        elif isinstance(value, str):
            try:
                return uuid.UUID(value)
            except Exception:
                pass
        raise FieldValidationError(FieldError(self, 'invalid'))
