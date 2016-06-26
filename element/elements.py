from element.abstract import AbstractField, ElementDefault
from element.exception import ElementException, InvalidElementException, SerializationException


class FieldErrorMessages():

    def __init__(self, *args, **kwargs):
        self._messages = {
            'invalid': 'Invalid Field',
            'required': 'Required Field'
        }
        self._messages.update(kwargs)


class MetaField(type):

    def __new__(cls, name, bases, attrs):
        klass = type.__new__(cls, name, bases + (AbstractField,), dict(attrs))
        if isinstance(attrs.get('messages'), FieldErrorMessages):
            klass.messages = attrs.get('messages')
        else:
            klass.messages = FieldErrorMessages(**attrs.get('messages', {}))
        if getattr(klass, 'new', None):
            constructor = klass.__init__
            new_constructor = klass.new
            def field_init(self, *args, **kwargs):
                constructor(self, *args, **kwargs)
                new_constructor(self, *args, **kwargs)
            klass.__init__ = field_init
            delattr(klass, 'new')
        return klass


class Field(metaclass=MetaField):

    def __init__(self, *args, **kwargs):
        self.name = kwargs.get('name', None)
        self.required = kwargs.get('required', False)
        self.default = kwargs.get('default', ElementDefault)
        self.allow_none = kwargs.get('allow_none', False)
        self._messages = kwargs.get('messages', {})

    def serialize(self, value):
        raise NotImplementedError

    def validate(self, value):
        raise NotImplementedError

    def message(self, name):
        if self._messages.get(name):
            return self._messages[name]
        else:
            return self.messages._messages[name]


class String(Field):

    messages = {'invalid': 'Field is not a valid String'}

    def serialize(self, value):
        if isinstance(value, str):
            return str(value)
        raise SerializationException

    def validate(self, value):
        if str(value) != value:
            raise InvalidElementException(self.message('invalid'))


class Integer(Field):

    messages = {'invalid': 'Field is not a valid Integer'}

    def serialize(self, value):
        if isinstance(value, int) and type(value) == int:
            return value
        raise SerializationException

    def validate(self, value):
        if not isinstance(value, int) or (type(value) != int):
            raise InvalidElementException(self.message('invalid'))


class Boolean(Field):

    def serialize(self, value):
        if isinstance(value, bool) and type(value) == bool:
            if value:
                return True
            return False
        raise SerializationException

    def validate(self, value):
        if not isinstance(value, bool) or (type(value) != bool):
            raise InvalidElementException(self.message('invalid'))


class Dict(Field):

    def serialize(self, value):
        if isinstance(value, dict):
            return value
        raise SerializationException

    def validate(self, value):
        if not isinstance(value, dict):
            raise InvalidElementException(self.message('invalid'))


class List(Field):

    messages = {'invalid_item': 'Field item is invalid'}

    def new(self, *args, **kwargs):
        self.field = kwargs.get('of', String())
        self.items = kwargs.get('items', [])

    def serialize(self, value):
        data = []
        for k, v in enumerate(value):
            try:
                value = self.field.serialize(v)
                data.append(value)
            except SerializationException:
                pass
        return data

    def validate(self, value):
        errors = {}
        if not isinstance(value, list):
            raise InvalidElementException(self.message('invalid'))
        for k, v in enumerate(value):
            try:
                self.field.validate(v)
            except ElementException as e:
                errors[k] = e
        if errors:
            raise InvalidElementException(self.message('invalid_item'), errors=errors)


