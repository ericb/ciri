import uuid

from ciri.exception import FieldValidationError
from ciri.fields import Field, FieldError


class UUID(Field):

    messages = {'invalid': 'Field is not a valid UUID'}

    def serialize(self, value):
        if isinstance(value, uuid.UUID):
            return str(value)
        if isinstance(value, str):
            return str(uuid.UUID(value))
        raise SerializationException

    def validate(self, value):
        if isinstance(value, uuid.UUID):
            return
        elif isinstance(value, str):
            try:
                return uuid.UUID(value)
            except Exception:
                pass
        raise FieldValidationError(FieldError(self, 'invalid'))
