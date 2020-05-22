import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')  # noqa

from ciri import fields
from ciri.core import Schema, SchemaOptions
from ciri.registry import SchemaRegistry, schema_registry
from ciri.exception import ValidationError, SerializationError

import pytest


def test_json_encode():
    class S(Schema):
        name = fields.String()
    schema = S()
    assert schema.encode({'name': 'bob'}) == '{"name": "bob"}'

def test_complex_json_encode():
    class S(Schema):
        name = fields.String()

    class Node(Schema):
        label = fields.String(required=True)
        sub = fields.Schema(S, required=True)

    class Root(Schema):
        node = fields.Schema(Node, required=True)

    schema = Root(node=Node(label='testing', sub=S(name='bob')))
    encoded = schema.encode()
    assert json.loads(encoded) == json.loads('{"node": {"label": "testing", "sub": {"name": "bob"}}}')
