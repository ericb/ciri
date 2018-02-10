.. ciri documentation master file, created by
   sphinx-quickstart on Wed Jan 31 00:48:29 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Ciri
================================

Ciri helps you build schema definitions for your application; giving you a foundation to perform validation, serialization and encoding. 

.. literalinclude:: /examples/basic_example.py


Features
========

* Python 3/2 support
* Serialize data to basic Python types 
* Deserialize data back to schema objects
* Schema encoding
* Polymorphic schemas
* Composable Fields
* Controllable error handling
* Pre/post processors available on fields
* Simple API


What makes Ciri different?
==========================

Ciri was built with a focus on ease of use, a cogent api, and faster execution. 


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   usage
   api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`



Testing
::

    from ciri import fields, Schema
    from ciri.exception import ValidationError
    
    class Person(Schema):
        name = fields.String()
        age = fields.Integer()
    
    class Parent(Person):
        child = fields.Schema(Person)
    
    # Create an instance of a child and a father
    father = Parent(name='Jack', age=52,
                    child=Person(name='Sarah', age=17))
    
    # Serialize the Parent
    try:
        serialized = father.serialize()
    except ValidationError:
        # the validate method is called by default when serializing
        errors = father.errors
    
    assert serialized == {'name': 'Jack', 'age': 52, 'child': {'name': 'Sarah', 'age': 17}}
