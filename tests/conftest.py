import pytest

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')

from element.core import Element
from element import elements


@pytest.fixture
def person():
    class Person(Element):
        name = elements.String()

    return Person(name='jack')
