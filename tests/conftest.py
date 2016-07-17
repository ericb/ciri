import pytest

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')

from ciri.core import Schema
from ciri import fields


@pytest.fixture
def person():
    class Person(Schema):
        name = fields.String()

    return Person(name='jack')
