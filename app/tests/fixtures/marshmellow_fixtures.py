from marshmallow import Schema, fields, post_load
from app.tests.fixtures.data_fixtures import User


class UserSchema(Schema):
    name = fields.Str()
    email = fields.Email()
    created_at = fields.DateTime()


class UserSchemaWichPostLoad(Schema):
    # In order to deserialize to an object, define a method of your
    # Schema and decorate it with post_load. The method receives a dictionary of deserialized data.    name = fields.Str()
    name = fields.Str()
    email = fields.Email()
    created_at = fields.DateTime()

    @post_load
    def make_user(self, data, **kwargs):
        return User(**data)


class TaskSchema(Schema):
    title = fields.Str()


class CleintSchema(Schema):
    name = fields.Str()
    email = fields.Email()
    created_at = fields.DateTime()
    tasks = fields.List(fields.Nested(TaskSchema))


class CleintSchemaFlat(Schema):
    name = fields.Str()
    email = fields.Email()
    created_at = fields.DateTime()
    tasks = fields.Pluck(TaskSchema, "title", many=True)
