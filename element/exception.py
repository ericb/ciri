class ElementException(Exception):
    pass

class InvalidElementException(ElementException):

    def __init__(self, message='', errors=None, *args, **kwargs):
        super().__init__(message, *args, **kwargs)
        if errors:
            self._errors = errors

class SerializationException(Exception):
    pass
