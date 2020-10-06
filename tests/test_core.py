import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../')  # noqa

import uuid

from ciri import fields
from ciri.fields import FieldError
from ciri.core import Schema, SchemaOptions
from ciri.registry import SchemaRegistry, schema_registry
from ciri.exception import ValidationError, SerializationError, FieldValidationError

import pytest


def test_empty_serialization():
    schema = Schema()
    schema.serialize({})
    assert schema.errors == {}


def test_empty_validation():
    schema = Schema()
    schema.validate({})
    assert schema.errors == {}


def test_default_callable():
    def make_name(schema, field):
        return 'audrey'

    class S(Schema):
        name = fields.String(default=make_name, output_missing=True)
    schema = S()
    assert schema.serialize({}) == {'name': 'audrey'}


def test_multiple_invalid_fields():
    class S(Schema):
        name = fields.String(required=True)
        age = fields.Integer(required=True)

    errors = {'name': {'msg': fields.String().message.invalid},
              'age': {'msg': fields.Integer().message.invalid}}

    schema = S()
    with pytest.raises(ValidationError):
        schema.serialize({'name': 33, 'age': '33'})
    assert schema.errors == errors


def test_schema_kwargs():
    class Sub(Schema):
        hello = fields.String(required=True)

    class S(Schema):
        name = fields.String(required=True)
        active = fields.Boolean()
        sub = fields.Schema(Sub)

    schema = S(name='ciri', active=True, sub=Sub(hello='testing'))
    assert schema.serialize() == {'name': 'ciri', 'active': True, 'sub': {'hello': 'testing'}}


def test_subclass_schema():
    class Person(Schema):
        name = fields.String()
        age = fields.Integer()

    class Parent(Person):
        child = fields.Schema(Person)

    child = Person(name='Sarah', age=17)
    father = Parent(name='Jack', age=52, child=child)

    assert father.serialize() == {'name': 'Jack', 'age': 52, 'child': {'name': 'Sarah', 'age': 17}}


def test_subclass_override_schema():
    class Person(Schema):
        name = fields.String(allow_empty=True)
        age = fields.Integer()

    class Parent(Person):
        name = fields.String(allow_empty=False)
        child = fields.Schema(Person)

    child = Person(name='', age=17)
    father = Parent(name='Jack', age=52, child=child)

    assert father.serialize() == {'name': 'Jack', 'age': 52, 'child': {'name': '', 'age': 17}}


def test_double_subclass_schema():
    class Person(Schema):
        name = fields.String()
        age = fields.Integer()

    class Parent(Person):
        child = fields.Schema(Person)

    class Father(Parent):
        sex = fields.String(default='male', output_missing=True)

    child = Person(name='Sarah', age=17)
    father = Father(name='Jack', age=52, child=child)

    assert father.serialize() == {'sex': 'male', 'name': 'Jack', 'age': 52, 'child': {'name': 'Sarah', 'age': 17}}


def test_errors_reset():
    class S(Schema):
        name = fields.String(required=True)
    schema = S()
    with pytest.raises(ValidationError):
        schema.serialize({})
    schema.serialize({'name': 'pi'})
    assert not schema.errors


def test_schema_opts_cls():
    opts = SchemaOptions()
    assert opts.allow_none == False


def test_schema_opts_cls_overrides():
    opts = SchemaOptions(allow_none=True)
    assert opts.allow_none == True


def test_schema_opts_allow_none_used():
    opts = SchemaOptions(allow_none=True)
    class S(Schema):
        name = fields.String()
    schema = S()
    schema.config({'options': opts})
    assert schema.serialize({'name': None}) == {'name': None}


def test_schema_opts_set_on_definition():
    class S(Schema):
        class Meta:
           options = SchemaOptions(allow_none=True)
        name = fields.String()

    schema = S()
    assert schema.serialize({'name': None}) == {'name': None}


def test_schema_raise_errors_false():
    class S(Schema):
        __schema_options__ = SchemaOptions(raise_errors=False)
        name = fields.String(required=True)

    schema = S()
    schema.serialize({})
    assert schema._raw_errors['name'].message == fields.String().message.required


def test_simple_validator_with_invalid_value():
    def validate_mark(value, schema=None, field=None):
        if value == 'mark':
            return value
        raise FieldValidationError(FieldError(field, 'invalid'))

    class S(Schema):
        name = fields.String(post_validate=[validate_mark])
    schema = S()
    with pytest.raises(ValidationError):
        schema.serialize({'name': 'bob'})
    assert schema._raw_errors['name'].message == fields.String().message.invalid

def test_simple_validator_with_valid_value():
    def validate_mark(value, schema=None, field=None):
        if value == 'mark':
            return value
        raise FieldValidationError(FieldError(field, 'invalid'))

    class S(Schema):
        name = fields.String(post_validate=[validate_mark])
    schema = S()
    assert schema.serialize({'name': 'mark'}) == {'name': 'mark'}


def test_multiple_validators_with_invalid_value():
    def validate_mark(value, schema=None, field=None):
        if value == 'mark':
            return value
        raise FieldValidationError(FieldError(field, 'invalid'))

    def is_integer(value, **kwargs):
        if not isinstance(value, int):
            return False
        return True

    class S(Schema):
        name = fields.String(post_validate=[validate_mark, is_integer])
    schema = S()
    with pytest.raises(ValidationError):
        schema.serialize({'name': 'marcus'})
    assert schema._raw_errors['name'].message == fields.String().message.invalid


def test_multiple_validators_with_valid_value():
    def validate_mark(value, **kwargs):
        if value == 'mark':
            return True
        return False

    def is_integer(value, **kwargs):
        if not isinstance(value, int):
            return True
        return False

    class S(Schema):
        name = fields.String(validators=[validate_mark, is_integer])
    schema = S()
    assert schema.serialize({'name': 'mark'}) == {'name': 'mark'}


def test_field_serialization_name():
    class S(Schema):
        name = fields.String(name='first_name')
    schema = S()
    assert schema.serialize({'name': 'Tester'}) == {'first_name': 'Tester'}

def test_field_serialization_name_missing():
    class S(Schema):
        class Meta:
           options = SchemaOptions(output_missing=True)
        name = fields.String(name='first_name')
    schema = S()
    assert schema.serialize({'notname': 'Tester'}) == {'first_name': None}

def test_field_serialization_load_key():
    class S(Schema):
        name = fields.String(load='testing', name='first_name')
    schema = S()
    assert schema.serialize({'name': 'Tester'}) == {'first_name': 'Tester'}


def test_simple_field_pre_validate():
    def not_fiona(value, **kwargs):
        if value == 'fiona':
            raise FieldValidationError(FieldError(self, 'invalid'))
        return value

    class S(Schema):
        first_name = fields.String(pre_validate=[not_fiona])
        last_name = fields.String()

    schema = S()
    assert schema.serialize({'first_name': 'foo bar', 'last_name': 'jenkins'}) == {'first_name': 'foo bar', 'last_name': 'jenkins'}


def test_simple_field_post_validate():
    def not_fiona(value, **kwargs):
        if value == 'fiona':
            raise FieldValidationError(FieldError(self, 'invalid'))
        return value

    class S(Schema):
        first_name = fields.String(post_validate=[not_fiona])
        last_name = fields.String()

    schema = S()
    assert schema.serialize({'first_name': 'foo bar', 'last_name': 'jenkins'}) == {'first_name': 'foo bar', 'last_name': 'jenkins'}


def test_simple_pre_field_validate_error():
    def not_fiona(value, schema=None, field=None):
        if value == 'fiona':
            raise FieldValidationError(FieldError(field, 'invalid'))
        return value

    class S(Schema):
        first_name = fields.String(pre_validate=[not_fiona])
        last_name = fields.String()

    schema = S()
    with pytest.raises(ValidationError):
        schema.serialize({'first_name': 'fiona', 'last_name': 'jenkins'})
    assert schema._raw_errors['first_name'].message == fields.String().message.invalid


def test_simple_field_pre_serializer():
    def capitilize(value, schema, field):
        return value.title()

    class S(Schema):
        first_name = fields.String(pre_serialize=[capitilize])
        last_name = fields.String()

    schema = S()
    assert schema.serialize({'first_name': 'foo bar', 'last_name': 'jenkins'}) == {'first_name': 'Foo Bar', 'last_name': 'jenkins'}


def test_field_name_change_pre_serializer():
    def capitilize(value, schema, field):
        return value.title()

    class S(Schema):
        first_name = fields.String(name='first', pre_serialize=[capitilize])
        last_name = fields.String()

    schema = S()
    assert schema.serialize({'first_name': 'foo bar', 'last_name': 'jenkins'}) == {'first': 'Foo Bar', 'last_name': 'jenkins'}


def test_simple_field_post_serializer():
    def capitilize(value, schema, field):
        return value.title()

    class S(Schema):
        first_name = fields.String(post_serialize=[capitilize])
        last_name = fields.String()

    schema = S()
    assert schema.serialize({'first_name': 'foo bar', 'last_name': 'jenkins'}) == {'first_name': 'Foo Bar', 'last_name': 'jenkins'}


def test_field_name_change_post_serializer():
    def capitilize(value, schema, field):
        return value.title()

    class S(Schema):
        first_name = fields.String(name='first', post_serialize=[capitilize])
        last_name = fields.String()

    schema = S()
    assert schema.serialize({'first_name': 'foo bar', 'last_name': 'jenkins'}) == {'first': 'Foo Bar', 'last_name': 'jenkins'}


def test_simple_field_pre_deserializer():
    def capitilize(value, schema, field):
        return value.title()

    class S(Schema):
        first_name = fields.String(pre_deserialize=[capitilize])
        last_name = fields.String()

    schema = S()
    s = schema.deserialize({'first_name': 'foo bar', 'last_name': 'jenkins'})
    assert s.first_name == 'Foo Bar'


def test_field_name_change_pre_deserializer():
    def capitilize(value, schema, field):
        return value.title()

    class S(Schema):
        first_name = fields.String(load='first', pre_deserialize=[capitilize])
        last_name = fields.String()

    schema = S()
    s = schema.deserialize({'first': 'foo bar', 'last_name': 'jenkins'})
    assert s.first_name == 'Foo Bar'


def test_simple_field_post_deserializer():
    def capitilize(value, schema, field):
        return value.title()

    class S(Schema):
        first_name = fields.String(post_deserialize=[capitilize])
        last_name = fields.String()

    schema = S()
    s = schema.deserialize({'first_name': 'foo bar', 'last_name': 'jenkins'})
    assert s.first_name == 'Foo Bar'


def test_field_name_change_post_deserializer():
    def capitilize(value, schema, field):
        return value.title()

    class S(Schema):
        first_name = fields.String(load='first', post_deserialize=[capitilize])
        last_name = fields.String()

    schema = S()
    s = schema.deserialize({'first': 'foo bar', 'last_name': 'jenkins'})
    assert s.first_name == 'Foo Bar'


def test_method_field_pre_validate():
    class S(Schema):
        name = fields.String(pre_validate=['not_bella'])

        def not_bella(self, value, schema=None, field=None):
            if value == 'bella':
                raise FieldValidationError(FieldError(field, 'invalid'))
            return value

    schema = S()
    assert schema.serialize({'name': 'sybil'}) == {'name': 'sybil'}


def test_failing_field_pre_validate():
    class S(Schema):
        name = fields.String(pre_validate=['not_bella'])

        def not_bella(self, value, field=None, **kwargs):
            if value == 'bella':
                raise FieldValidationError(FieldError(field, 'invalid'))
            return value

    schema = S()
    with pytest.raises(ValidationError):
        schema.serialize({'name': 'bella'})
    assert schema._raw_errors['name'].message == fields.String().message.invalid


def test_schema_include():
    class A(Schema):
        a = fields.String()

    class B(Schema):
        b = fields.String()

    class C(Schema):
        c = fields.String()

    class ABC(Schema):
        __schema_include__ = [A, B, C]

    schema = ABC()
    assert sorted(list(schema._fields.keys())) == ['a', 'b', 'c']


def test_schema_include_as_mapping():
    base_fields = {'a': fields.String(), 'b': fields.String()}

    class ABC(Schema):
        __schema_include__ = [base_fields]

        c = fields.String()

    schema = ABC()
    assert sorted(list(schema._fields.keys())) == ['a', 'b', 'c']


def test_schema_include_with_override():
    class A(Schema):
        a = fields.String()

    class B(Schema):
        b = fields.String()

    class C(Schema):
        c = fields.String()

    class ABC(Schema):
        __schema_include__ = [A, B, C]

        b = fields.Integer()

    schema = ABC()
    assert isinstance(schema._fields['b'], fields.Integer)


def test_schema_compose():
    class A(Schema):
        a = fields.String()

    class B(Schema):
        b = fields.String()

    class C(Schema):
        c = fields.String()

    class ABC(Schema):

        class Meta:
            compose = [A, B, C]

        b = fields.Integer()

    schema = ABC()
    assert isinstance(schema._fields['c'], fields.String)


def test_schema_field_remove():
    class A(Schema):
        a = fields.String()

    class B(Schema):
        b = fields.String()

    class C(Schema):
        c = fields.String()

    class ABRemoveC(C, B, A):

        b = fields.Integer()
        c = None

    schema = ABRemoveC(a='a', b=7, c='c')
    assert schema.serialize() == {'a': 'a', 'b': 7}


def test_exclude_all_fields():
    class A(Schema):
        a = fields.String()
    assert A(a='a').serialize(exclude=['a']) == {}

def test_exclude_single_field():
    class ABC(Schema):
        a = fields.String()
        b = fields.String()
        c = fields.String()
    assert ABC(a='a', b='b').serialize(exclude=['a']) == {'b': 'b'}

def test_exclude_multiple_fields():
    class ABC(Schema):
        a = fields.String()
        b = fields.String()
        c = fields.String()
    assert ABC(a='a', b='b').serialize(exclude=['a', 'b']) == {}

def test_exclude_required_field():
    class ABC(Schema):
        a = fields.String(required=True)
        b = fields.String()
        c = fields.String()
    assert ABC(b='b').serialize(exclude=['a']) == {'b': 'b'}

def test_exclude_self_reference():
    class ABC(Schema):
        a = fields.String()
        abc = fields.SelfReference(exclude=['abc'])
    assert ABC(a='root', abc=ABC(a='nested', abc=ABC(a='sublevel'))).serialize() == {'a': 'root', 'abc': {'a': 'nested'}}

def test_exclude_schema_reference():
    class Sub(Schema):
        hello = fields.String(required=True)

    class S(Schema):
        name = fields.String(required=True)
        active = fields.Boolean()
        sub = fields.Schema(Sub, exclude=['hello'])

    schema = S(name='ciri', active=True, sub=Sub(hello='testing'))
    assert schema.serialize() == {'name': 'ciri', 'active': True, 'sub': {}}

def test_default_missing_output_value():
    class S(Schema):
        class Meta:
           options = SchemaOptions(output_missing=True)
        name = fields.String()

    schema = S()
    errors = {}
    assert schema.serialize({}) == {'name': None}

def test_basic_whitelist():
    class ABC(Schema):
        a = fields.String()
        b = fields.String()
        c = fields.String()
    assert ABC(a='a', b='b', c='c').serialize(whitelist=['a', 'b']) == {'a': 'a', 'b': 'b'}

def test_basic_whitelist_with_exclude():
    class ABC(Schema):
        a = fields.String()
        b = fields.String()
        c = fields.String()
    assert ABC(a='a', b='b', c='c').serialize(exclude=['b'], whitelist=['a', 'b']) == {'a': 'a'}

def test_whitelist_on_schema_field():
    class Sub(Schema):
        hello = fields.String(required=True)
        world = fields.String(required=True)

    class S(Schema):
        name = fields.String(required=True)
        active = fields.Boolean()
        sub = fields.Schema(Sub, whitelist=['hello'])

    schema = S(name='ciri', active=True, sub=Sub(hello='testing'))
    assert schema.serialize() == {'name': 'ciri', 'active': True, 'sub': {'hello': 'testing'}}

def test_whitelist_on_self_ref():
    class ABC(Schema):
        a = fields.String()
        abc = fields.SelfReference(whitelist=['a'])
    assert ABC(a='root', abc=ABC(a='nested', abc=ABC(a='sublevel'))).serialize() == {'a': 'root', 'abc': {'a': 'nested'}}

def test_whitelist_on_self_ref_with_exclude():
    class ABC(Schema):
        a = fields.String()
        abc = fields.SelfReference(whitelist=['a'])
    assert ABC(a='root', abc=ABC(a='nested', abc=ABC(a='sublevel'))).serialize(exclude=['a']) == {'abc': {'a': 'nested'}}

def test_whitelist_on_self_ref_with_nested_exclude():
    class ABC(Schema):
        a = fields.String()
        abc = fields.SelfReference(whitelist=['a'], exclude=['a'])
    assert ABC(a='root', abc=ABC(a='nested', abc=ABC(a='sublevel'))).serialize() == {'a': 'root', 'abc': {}}

@pytest.mark.parametrize("role, expected", [
    ['a', {'a': 'a'}],
    ['ab', {'a': 'a', 'b': 'b'}],
    ['all', {'a': 'a', 'b': 'b', 'c': 'c'}]
])
def test_basic_output_tag(role, expected):
    class ABC(Schema):

        __field_tags__ = {'a': ['a'], 'ab': ['a', 'b'], 'all': ['a', 'b', 'c']}

        a = fields.String()
        b = fields.String()
        c = fields.String()

    schema = ABC(a='a', b='b', c='c')
    assert schema.serialize(tags=[role]) == expected


@pytest.mark.parametrize("role, expected", [
    ['a', {'a': 'a'}],
    ['ab', {'a': 'a', 'b': 'b'}],
    ['all', {'a': 'a', 'b': 'b', 'c': 'c'}]
])
def test_meta_output_tag(role, expected):
    class ABC(Schema):

        a = fields.String(tags=['a', 'ab', 'all'])
        b = fields.String(tags=['ab', 'all'])
        c = fields.String(tags=['all'])

    schema = ABC(a='a', b='b', c='c')
    assert schema.serialize(tags=[role]) == expected


def test_tag_mixed_with_exclude():
    class ABC(Schema):
        a = fields.String(tags=['a', 'ab', 'all'])
        b = fields.String(tags=['ab', 'all'])
        c = fields.String(tags=['all'])

    schema = ABC(a='a', b='b', c='c')
    assert schema.serialize(exclude=['a'], tags=['ab']) == {'b': 'b'}


def test_tag_mixed_with_whitelist_and_exclude():
    class ABC(Schema):
        a = fields.String(tags=['a', 'ab', 'all'])
        b = fields.String(tags=['ab', 'all'])
        c = fields.String(tags=['all'])

    schema = ABC(a='a', b='b', c='c')
    assert schema.serialize(whitelist=['a', 'b', 'c'], exclude=['a'], tags=['ab']) == {'b': 'b'}


def test_schema_callable():
    class ABC(Schema):

        __schema_callables__ = {
            'pre_serialize': ['d_e_f']
        }

        a = fields.String()
        b = fields.String()
        c = fields.String()

        def d_e_f(self, data, **kwargs):
            data['a'] = 'd'
            data['b'] = 'e'
            data['c'] = 'f'
            return data

    schema = ABC(a='a', b='b', c='c')
    assert schema.serialize() == {'a': 'd', 'b': 'e', 'c': 'f'}

def test_meta_schema_callable():
    class ABC(Schema):

        class Meta:
            pre_serialize = 'd_e_f'

        a = fields.String()
        b = fields.String()
        c = fields.String()

        def d_e_f(self, data, **kwargs):
            data['a'] = 'd'
            data['b'] = 'e'
            data['c'] = 'f'
            return data

    schema = ABC(a='a', b='b', c='c')
    assert schema.serialize() == {'a': 'd', 'b': 'e', 'c': 'f'}

def test_schema_context():
    class ABC(Schema):

        class Meta:
            pre_serialize = 'd_e_f'

        a = fields.String()
        b = fields.String()
        c = fields.String()

        def d_e_f(self, data, context=None, **kwargs):
            for x in context:
                data[x] = context[x]
            return data

    schema = ABC(a='a', b='b', c='c')
    schema.context.update({'a': 'd', 'b': 'e', 'c': 'f'})
    assert schema.serialize() == {'a': 'd', 'b': 'e', 'c': 'f'}

def test_schema_serialize_context():
    class ABC(Schema):

        class Meta:
            pre_serialize = 'd_e_f'

        a = fields.String()
        b = fields.String()
        c = fields.String()

        def d_e_f(self, data, context=None, **kwargs):
            for x in context:
                data[x] = context[x]
            return data

    schema = ABC(a='a', b='b', c='c')
    schema.context = {'a': 'a'}
    ctx = {'a': 'd', 'b': 'e', 'c': 'f'}
    assert schema.serialize(context=ctx) == {'a': 'd', 'b': 'e', 'c': 'f'}

def test_schema_elements_have_load():
    class S(Schema):
        name = fields.Child(fields.String(name='title'), load='nest')
    schema = S()
    assert schema.deserialize({'foo': 'bar', 'nest': {'title': 'Hello World'}}).serialize() == {'name': 'Hello World'}

def test_schema_elements_have_load_with_data_object():
    class S(Schema):
        name = fields.Child(fields.String(name='title'), load='nest')
    schema = S()
    class Data: pass
    data = Data()
    data.foo = 'bar'
    data.nest = Data()
    data.nest.title = 'Hello World'
    assert schema.deserialize(data).serialize() == {'name': 'Hello World'}

def test_schema_multiple_elements_have_load():
    class S(Schema):
        name = fields.Child(fields.String(name='title'), load='nest')
        name2 = fields.Child(fields.String(name='title2'), load='nest')
    schema = S()
    assert schema.deserialize({'foo': 'bar', 'nest': {'title': 'Hello World', 'title2': 'Hello World 2'}}).serialize() \
        == {'name': 'Hello World', 'name2': 'Hello World 2'}

def test_schema_elements_have_load_with_path():
    class S(Schema):
        name = fields.Child(fields.String(name='title'), path='b.c', load='a')
    schema = S()
    assert schema.serialize({'name': {'b': {'c': {'title': 'Hello World'}}}}) == {'name': 'Hello World'}

def test_schema_elements_have_load_with_path_and_data_object():
    class S(Schema):
        name = fields.Child(fields.String(name='title'), path='b.c', load='a')
    schema = S()
    class Data: pass
    data = Data()
    data.name = Data()
    data.name.b = {'c': Data()}
    data.name.b['c'].title = 'Hello World'
    assert schema.serialize(data) == {'name': 'Hello World'}

def test_schema_elements_uuid():
    genid = uuid.uuid4()
    class S(Schema):
        rec_id = fields.Child(fields.UUID(name='id'), path='b.c', load='rec')
    schema = S()
    class Data: pass
    data = Data()
    data.rec = Data()
    data.rec.b = {'c': Data()}
    data.rec.b['c'].id = genid
    assert schema.deserialize(data).serialize() == {'rec_id': str(genid)}

def test_deserialize_with_load():
    class S(Schema):
        first_name = fields.String(load='first')
        last_name = fields.String()

    schema = S()
    s = schema.deserialize({'first': 'foo bar', 'last_name': 'jenkins'})
    assert s.first_name == 'foo bar'

def test_output_missing_with_default():
    class S(Schema):
        first_name = fields.String(default='first')
        last_name = fields.String(default='last')
    schema = S()
    output = schema.serialize({})
    assert output == {}


def test_schema_subschema_elements_have_load():
    class S(Schema):
        name_ = fields.String(name='name', load='name')

    class Parent(Schema):
        sub = fields.Schema(S)

    schema = Parent()
    obj = schema.deserialize({'sub': {'name': 'TheFalcon'}})
    assert obj == Parent(sub=S(name_='TheFalcon'))
    assert obj.serialize() == {'sub': {'name': 'TheFalcon'}}


def test_schema_parent_schema_element_has_load():
    class S(Schema):
        name = fields.String()

    class Parent(Schema):
        sub_ = fields.Schema(S, load='sub', name='sub')

    schema = Parent()
    obj = schema.deserialize({'sub': {'name': 'TheFalcon'}})
    assert obj == Parent(sub_=S(name='TheFalcon'))
    assert obj.serialize() == {'sub': {'name': 'TheFalcon'}}
