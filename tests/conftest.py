import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')  # noqa

import pytest

from ciri import fields
from ciri.core import Schema
