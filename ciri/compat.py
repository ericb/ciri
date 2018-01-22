import sys

# check python type
py2 = False
py3 = False

if sys.version_info[0] < 3:
    py2 = True
    py3 = False
else:
    py2 = False
    py3 = True


# six 1.9.0
# https://github.com/kelp404/six/blob/30b8641f5b25e095c1f7ca1c8b82b3c0f9925f48/six.py#L782-L795
def add_metaclass(metaclass):
    """Class decorator for creating a class with a metaclass."""
    def wrapper(cls):
        orig_vars = cls.__dict__.copy()
        slots = orig_vars.get('__slots__')
        if slots is not None:
            if isinstance(slots, str):
                slots = [slots]
            for slots_var in slots:
                orig_vars.pop(slots_var)
        orig_vars.pop('__dict__', None)
        orig_vars.pop('__weakref__', None)
        return metaclass(cls.__name__, cls.__bases__, orig_vars)
    return wrapper


str_ = str
if py2:
    str_ = unicode
