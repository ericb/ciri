import os
import sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')  # noqa

from ciri.fields import Dict
from ciri.core import Schema
from ciri.exception import ValidationError

import pytest


@pytest.mark.parametrize("value", [
    1,
    '1',
    [],
    OrderedDict,
    {'bar1', 'bar2'},
    Schema
])
def test_invalid_values(value):
    class S(Schema):
        foo = Dict()
    schema = S()
    with pytest.raises(ValidationError):
        schema.serialize({'foo': value})
    assert schema.raw_errors['foo'].message == Dict().message.invalid


def test_dict_subclass():
    class S(Schema):
        foo = Dict()
    schema = S()
    o = OrderedDict({'a': 'b'})
    assert schema.serialize({'foo': o}) == {'foo': {'a': 'b'}}
