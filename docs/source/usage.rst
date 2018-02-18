Usage
=====


Schemas
#######

Schemas are defined by subclassing :class:`~ciri.core.Schema` and defining fields as class properties.

::

   import datetime
   from ciri import fields, Schema, ValidationError


   class User(Schema):
       name = fields.String(required=True)
       type_ = fields.String(name='type', required=True)
       created = fields.Date()


   user = User(name='Eric', type_='dev', created=datetime.date(2018, 1, 1))
   user.serialize()

   # {'name': Eric', 'type': 'dev', 'created': '2018-01-01'}


Schema Options
--------------

All schemas have a :class:`~ciri.core.SchemaOptions` object which sets the default behavior. You can
configure your own defaults by setting the `__schema_options__` property in your schema definition:

::

    from ciri import fields, Schema, SchemaOptions


    class Person(Schema):
   
        __schema_options__ = SchemaOptions(allow_none=True)
        
        name = fields.String()

    person = Person().serialize({})  # {'name': None} 


Subclassing
-----------

Schemas can be subclassed as you would normal objects. 

::

    class Person(Schema):
        name = fields.String()
        age = fields.Integer()


    class Parent(Person):
        # inherits name, age
        children = fields.List(Person())


    class GrandParent(Parent):
        # inherits name, age, children
        grandchildren = fields.List(Person())


Validating Data
---------------

Validate data using the :func:`~ciri.core.Schema.validate` method:

::

    class Person(Schema):
        name = fields.String(required=True)

    person = Person().serialize({})  # raises ValidationError


Raw validation errors are stored on the `_raw_errors` property. The schema error handler will also
compile error output to be used in your application and can be accessed through the `errors` property.
Check out the :ref:`error_handling` section for more details on what to do with validation errors.

.. _serializing_data:

Serializing Data
----------------

Data is serialized using the :func:`~ciri.core.Schema.serialize` method:

::

    class Person(Schema):
        name = fields.String(required=True)

    person = Person().serialize({'name': 'Harry'})  # {'name': 'Harry'}

You can also serialize a schema instance by passing no data to the serailize method:

::

   person = Person(name='Harry').serialize()  # {'name': Harry}


By default, :func:`~ciri.core.Schema.validate` is called serialization. You can skip validation
(if you have already validated elsewhere for example) by passing `skip_validation` to the
serialize method:

::

   person = Person(name=123).serialize(skip_validation=True)  # {'name': 123}

All serialization requires validation to correctly serialize, but if you are confident the data
being serialized is already valid, you can save time by skipping validation. This is useful if
you are serializing database output or other known values.


Deserializing Data
------------------

Data is deserialized using the :func:`~cir.core.Schema.deserialize` method. It behaves the same
way as the serialization method and has the same validation caveats. Check out the :ref:`serializing_data`
section for more info.

::

    class Person(Schema):
        name = fields.String(required=True)

    person = Person().deserialize({'name': 'Harry'})
    person.name  # Harry


Encoding Data
-------------

Data is encoded using the (you guessed it) :func:`~ciri.core.Schema.encode` method. By default, the 
:func:`~ciri.core.Schema.validate` and :func:`~ciri.core.Schema.serialize` methods will be called and
the resulting serialized data will be passed to the encoder. You can skip validation and serialization
using the `skip_validation` and `skip_serialization` keyword args.

The default encoder class is :class:`~ciri.encoder.JSONEncoder` but can be set in the schema options.

::

    class Person(Schema):
        name = fields.String()
        active = fields.Boolean(default=False)

    person = Person(name=Harry).encode()  # '{"name": "Harry", "active": false}'


.. _error_handling:

Error Handling
--------------

Things go wrong. It's important to know *why* they went wrong. When a field is invalid,
a :class:`~ciri.exception.FieldValidationError` is raised. The offending :class:`~ciri.fields.FieldError`
passed is then set on on the schemas `_raw_errors` dict under the key the field was defined as
on the schema (not the serialized output name). More often than not, you won't need to care about the
`_raw_errors` but it can be useful for testing and debugging.

By contrast, the `errors` property is very useful for error reporting. It holds the formatted error
output. The default error handler outputs errors that are structured like so:

::

    {'field_key': {'msg': 'Error Description'}}

So in effect:

::

    from ciri import fields, Schema, ValidationError


    class Person(Schema):

        name = fields.String(required=True) 
        age = fields.Integer(required=True) 
        born = fields.Date(required=True) 

    try:
        person = Person(name=Harry, age="42").serialize()
    except ValidationError:
        person.errors  # {'age': {'msg': 'Field is not a valid Integer'}, 'born': {'msg': 'Required Field'}}


Nested Errors
+++++++++++++

Sequence and Mapping fields such as :class:`~ciri.fields.List` and :class:`~ciri.fields.Schema` can
contain multiple errors. The default error handler will nest these errors under the `errors` key. 

Here is an example of nested errors:

::

    class Person(Schema):
    
        name = fields.String(required=True) 
        age = fields.Integer(required=True) 
        born = fields.Date(required=True) 
    
    
    class Sibling(Person):
    
        mother = fields.Schema(Person, required=True)
        siblings = fields.List(Person(), required=True)
        
    
    mother = Person(name='Karen', age="73", born='1937-06-17')
    brother = Person(name='Joe', age=45, born='1965-10-11')
    child = Sibling(name='Harry', age=42, mother=mother, siblings=[brother, 'sue'])
    try:
        child.serialize()
    except Exception as e:
        print(child.errors)

    # {'born': {'msg': 'Required Field'},
    #  'siblings': {'msg': 'Invalid Item(s)', 'errors': {'1': {'msg': 'Field is not a valid Mapping'}}},
    #  'mother': {'msg': 'Invalid Schema', 'errors': {'age': {'msg': 'Field is not a valid Integer'}}}}

.. note::

    Sequence fields will use the sequence index (coerced with :class:`str`) as the error key. 


.. rst-class:: spacer

Polymorphic Schemas
###################

Polymorphic schemas let you define a set of derived schema variations. In other words, you can
define a base schema that can be mapped to another schema using an identifier that resides on
the schema itself.

Let's examine a small but practical use case for using polymorphism; versioning. Take this basic
user schema as an example:

::

    from ciri import PolySchema


    class AppUser(PolySchema):
    
        username = fields.String(required=True)
        email = fields.String(required=True)
        version = fields.String(default='v1')

        __poly_on__ = version  # define the field which will determine the subclass mapping


The **__poly_on__** attribute defines which schema field will be used to map subclasses. Notice
that we've also got the username and email fields. We can now use the *AppUser* schema to define
further variations.

::

    class AppUserV1(AppUser):

        __poly_id__ = 'v1'  # define the polymorphic identifier
        
        # add additional fields
        first_name = fields.String(required=True)
        last_name = fields.String()
        twitter_url = fields.String(allow_none=True)


    class AppUserV2(AppUserV1):

        __poly_id__ = 'v2'  # define the polymorphic identifier
        
        # add another field    
        roles = fields.List(fields.String())

        # modify another field
        last_name = fields.String(required=True)


Above we've used the **__poly_id__** attribute to define a *v1* and *v2* schema mapping. Notice how you can continue to subclass the original
:class:`~ciri.core.PolySchema`. Now let's see what makes these mappings so handy.

::

        user_data = {
            'username': 'magic_is_cool',
            'email': 'hpotter@hogwarts.example.com',
            'first_name': 'Harry',
            'last_name': 'Potter',
            'roles': ['student', 'wizard']
        }

        v1_user = AppUser(version='v1', **user_data)
        # <AppUser object at 0x7f4441245e48>

        v2_user = AppUser(version='v2', **user_data)
        # <AppUser object at 0x7fd127dfae48>

        v1_user_again = AppUser.polymorph(version='v1', **user_data)
        # <AppUserV1 object at 0x7f64597520b8>

        v2_user_again = AppUser().deserialize(v2_user.serialize())
        # <AppUserV2 object at 0x7fd127dfaf28>


Notice that each of these interactions utilize the same base polymorphic schema class, but
will return different schema instances depending on the usage. This is important to know
when performing checks like :function:`isinstance`, but for most other intents and purposes,
they can be considered functionally equivalent.

Here's a bit of code that may make that more clear:

::

        print(isinstance(v1_user, AppUserV1))
        # False

        print(isinstance(v1_user_again, AppUserV1))
        # True

        print(v1_user.serialize() == v1_user_again.serialize())
        # True

.. rst-class:: spacer

Fields
#######

Field Type Reference
--------------------

.. list-table::
   :widths: auto 
   :header-rows: 1

   * - Class
     - Python Type
     - Notes
   * - :class:`~ciri.fields.String`
     - :class:`str`, :class:`unicode`
     - Returns the unicode type in python 2.x 
   * - :class:`~ciri.fields.Integer`
     - :class:`int` 
     -  
   * - :class:`~ciri.fields.Float`
     - :class:`float` 
     -  
   * - :class:`~ciri.fields.Dict`
     - :class:`dict` 
     -  
   * - :class:`~ciri.fields.Schema`
     - :class:`dict` 
     -  
   * - :class:`~ciri.fields.UUID`
     - :class:`str` 
     -  
   * - :class:`~ciri.fields.Date`
     - :class:`str` 
     - ISO-8601 Date String 
   * - :class:`~ciri.fields.DateTime`
     - :class:`str` 
     - ISO-8601 Date + Time String 
