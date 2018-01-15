# Ciri

A Python object serialization library.

## Simple Example

```python
from ciri import fields, Schema
from ciri.exception import ValidationError

class Person(Schema):
    name = fields.String()
    age = fields.Integer()

class Parent(Person):
    child = fields.Schema(Person)

# Create an instance of a child and a father
child = Person(name='Sarah', age=17)
father = Parent(name='Jack', age=52, child=child)

# Serialize the Parent
try:
    serialized = father.serialize()
except ValidationError:
    # the validate method is called by default when serializing
    errors = father.errors

assert serialized == {'name': 'Jack', 'age': 52, 'child': {'name': 'Sarah', 'age': 17}}
```
