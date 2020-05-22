import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')  # noqa

from ciri.fields import UUID
from ciri.core import Schema
from ciri.exception import ValidationError

import pytest


def test_valid_uuid():
    class U(Schema):
        id = UUID(required=True)
    schema = U()
    uid = uuid.uuid4()
    assert schema.serialize({'id': uid}) == {'id': str(uid)}


def test_valid_uuid_str():
    class U(Schema):
        id = UUID(required=True)
    schema = U()
    assert schema.serialize({'id': 'a8098c1a-f86e-11da-bd1a-00112444be1e'}) == {'id': 'a8098c1a-f86e-11da-bd1a-00112444be1e'}


@pytest.mark.parametrize("value", [
    1,
    True,
    False,
    {},
    [],
    {'bar1', 'bar2'},
    Schema
])
def test_invalid_values(value):
    class U(Schema):
        id = UUID(required=True)
    schema = U()
    with pytest.raises(ValidationError):
        schema.serialize({'id': value})
    assert schema._raw_errors['id'].message == UUID().message.invalid
