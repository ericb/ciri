# Element

A Python object serialization library.

## Example

```python
from element import elements
from element.core import Element

# Setup the Element object
class Person(Element):

    id = elements.Integer(required=True)
    name = elements.String()
    username = elements.String(required=True)


# Create an instance of the Element
employee = Person(id=4, name='Jack', username='coolguyjack')

# Serialize the Element
employee.serialize()

# employee._data
# {'id': 4, 'username': 'coolguyjack', 'name': 'Jack'}
```

