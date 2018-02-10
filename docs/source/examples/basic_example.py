import datetime

from ciri import fields, Schema, ValidationError


class Actor(Schema):

    first_name = fields.String()
    last_name = fields.String()


class Movie(Schema):

    title = fields.String()
    released = fields.Date()
    cast = fields.List(Actor())


movie = Movie()
output = movie.serialize({'title': 'Good Will Hunting',
                           'released': datetime.date(1998, 1, 9),
                           'cast': [
                               {'first_name': 'Matt', 'last_name': 'Damon'},
                               {'first_name': 'Ben', 'last_name': 'Affleck'},
                               {'first_name': 'Robin', 'last_name': 'Williams'}
                           ]})

# output:
# {'cast': [{'last_name': 'Damon', 'first_name': 'Matt'},
#           {'last_name': 'Affleck', 'first_name': 'Ben'},
#           {'last_name': 'Williams', 'first_name': 'Robin'}],
#  'released': '1998-01-09',
#  'title': 'Good Will Hunting'}
