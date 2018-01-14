import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')  # noqa

from ciri.fields import List, String, Float, Schema as SubSchema
from ciri.core import Schema
from ciri.exception import ValidationError

import pytest


class FooSchema(Schema):
    hello = String()


@pytest.mark.parametrize("value", [
    1,
    '1',
    True,
    {},
    {'bar1', 'bar2'},
    ('test', 'test2'),
    Schema
])
def test_invalid_values(value):
    class S(Schema):
        foo = List()
    schema = S()
    with pytest.raises(ValidationError):
        schema.serialize({'foo': value})
    assert schema.raw_errors['foo'].message == List().message.invalid

@pytest.mark.parametrize("item_type,value", [
    [String(), 1],
    [String(allow_empty=False), ''],
    [Float(), 1],
    [SubSchema(FooSchema), {'hello': 1}],
])
def test_invalid_items(item_type, value):
    class S(Schema):
        foo = List(of=item_type)
    schema = S()
    with pytest.raises(ValidationError):
        schema.serialize({'foo': [value]})
    assert schema.raw_errors['foo'].message == List().message.invalid_item
