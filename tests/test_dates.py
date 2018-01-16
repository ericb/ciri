import os
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')  # noqa

from ciri.fields import Date, DateTime
from ciri.core import Schema
from ciri.exception import ValidationError

import pytest


@pytest.mark.parametrize("value, expected", [
    ['2008-09-15', '2008-09-15'],
    ['2008-09-15T15:53:00', '2008-09-15'],
    ['2008-09-15T15:53:00Z', '2008-09-15'],
    ['2008-09-15T15:53:00+0000', '2008-09-15'],
    ['2008-09-15T15:53:00+00:00', '2008-09-15'],
    ['2008-09-15T15:53:00-05:00', '2008-09-15'],
])
def test_iso_8601_date_string(value, expected):
    class D(Schema):
        date = Date()
    schema = D()
    assert schema.serialize({'date': value}) == {'date': expected}


def test_iso_8601_date():
    class D(Schema):
        date = Date()
    schema = D()
    assert schema.serialize({'date': date(2008, 9, 15)}) == {'date': '2008-09-15'}


@pytest.mark.parametrize("value, expected", [
    ['2008-09-15T15:53:00', '2008-09-15T15:53:00'],
    ['2008-09-15T00:00:00', '2008-09-15T00:00:00'],
    ['2008-09-15T00:00:00Z', '2008-09-15T00:00:00+00:00'],
    ['2008-09-15T00:00:00+05:00', '2008-09-15T00:00:00+05:00'],
    ['2008-09-15T00:00:00-03:00', '2008-09-15T00:00:00-03:00']
])
def test_iso_8601_datetime_string(value, expected):
    class D(Schema):
        date = DateTime()
    schema = D()
    try:
        assert schema.serialize({'date': value}) == {'date': expected}
    except ValidationError as e:
        print(schema.errors)
        raise e


def test_iso_8601_datetime():
    class D(Schema):
        date = DateTime()
    schema = D()
    assert schema.serialize({'date': datetime(2008, 9, 15, 8, 5, 30)}) == {'date': '2008-09-15T08:05:30'}


@pytest.mark.parametrize("value", [
    1.00,
    '1',
    True,
    False,
    {},
    [],
    {'bar1', 'bar2'},
    Schema
])
def test_invalid_date_values(value):
    class D(Schema):
        date = Date()
    schema = D()
    with pytest.raises(ValidationError):
        schema.serialize({'date': value})
    assert schema._raw_errors['date'].message == Date().message.invalid


@pytest.mark.parametrize("value", [
    1.00,
    '1',
    True,
    False,
    {},
    [],
    {'bar1', 'bar2'},
    Schema
])
def test_invalid_datetime_values(value):
    class D(Schema):
        date = DateTime()
    schema = D()
    with pytest.raises(ValidationError):
        schema.validate({'date': value})
    assert schema._raw_errors['date'].message == DateTime().message.invalid
