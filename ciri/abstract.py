from abc import ABCMeta

from ciri.compat import add_metaclass


@add_metaclass(ABCMeta)
class AbstractField(object):
    pass

class SchemaFieldDefault(object):
    pass

class SchemaFieldMissing(object):
    pass
