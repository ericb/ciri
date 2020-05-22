import os
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')  # noqa

from ciri.util.dateparse import get_fixed_timezone
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
    assert schema.serialize({'date': value}) == {'date': expected}


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


@pytest.mark.parametrize("value, expected", [
    ['2008-09-15T15:53:00', datetime(2008, 9, 15, 15, 53, 0)],
    ['2008-09-15T00:00:00', datetime(2008, 9, 15, 0, 0, 0)],
    ['2008-09-15T00:00:00Z', datetime(2008, 9, 15, 0, 0, 0, tzinfo=get_fixed_timezone(0))],
    ['2008-09-15T00:00:00+05:00', datetime(2008, 9, 15, 0, 0, 0, tzinfo=get_fixed_timezone(60*5))],
    ['2008-09-15T00:00:00-03:00', datetime(2008, 9, 15, 0, 0, 0, tzinfo=get_fixed_timezone(-(60*3)))]
])
def test_datetime_deserialization(value, expected):
    class D(Schema):
        date = DateTime()
    schema = D()
    assert schema.deserialize({'date': value}) == D(date=expected)


@pytest.mark.parametrize("value, expected", [
    ['2008-09-15', date(2008, 9, 15)],
    ['2008-09-15T15:53:00', date(2008, 9, 15)],
    ['2008-09-15T15:53:00Z', date(2008, 9, 15)],
    ['2008-09-15T15:53:00+0000', date(2008, 9, 15)],
    ['2008-09-15T15:53:00+00:00', date(2008, 9, 15)],
    ['2008-09-15T15:53:00-05:00', date(2008, 9, 15)]
])
def test_date_deserialization(value, expected):
    class D(Schema):
        date = Date()
    schema = D()
    assert schema.deserialize({'date': value}) == D(date=expected)
