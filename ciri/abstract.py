from abc import ABCMeta


class AbstractField(object):
    pass


class AbstractBaseSchema(ABCMeta):

    def __new__(cls, name, bases, attrs):
        klass = ABCMeta.__new__(cls, name, bases, dict(attrs))
        klass._elements = {}
        klass._fields = {}
        for k, v in attrs.items():
            #print('hrm:', k, type(v), isinstance(v, AbstractField))
            if isinstance(v, AbstractField):
                klass._fields[k] = v
                delattr(klass, k)
                if v.required or v.allow_none or (v.default is not SchemaFieldDefault):
                    klass._elements[k] = True
            else:
                setattr(klass, k, v)
        return klass

# Type Definitions
SchemaFieldDefault = type('SchemaFieldDefault', (object,), {})
SchemaFieldMissing = type('SchemaFieldMissing', (object,), {})
