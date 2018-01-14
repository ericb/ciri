from ciri.exception import RegistryError

RegistryKeyMissing = type('RegistryKeyMissing', (object,), {})


class Registry(object):

    def __init__(self):
        self.init_registry()

    def init_registry(self):
        self.storage = {}

    def add(self, name, value):
        self.storage[name] = value

    def get(self, name, **kwargs):
        if 'default' in kwargs:
            return self.storage.get(name, kwargs.get('default'))
        else:
            reg_value = self.storage.get(name, RegistryKeyMissing)
            if reg_value != RegistryKeyMissing:
               return reg_value
            raise RegistryError('{} was not found in the registry'.format(name))
        

    def remove(self, name):
        del self.storage[name]

    def reset(self):
        self.init_registry()


class SchemaRegistry(Registry):
    pass


schema_registry = SchemaRegistry()
