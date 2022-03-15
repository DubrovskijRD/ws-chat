from marshmallow import Schema, fields, validate, post_load

from datetime import datetime


class Timestamp(fields.Int):

    def _serialize(self, value, attr, obj, **kwargs):
        if value:
            value = value.timestamp()
        return super()._serialize(value, attr, obj, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        value = super()._deserialize(value, attr, data, **kwargs)
        return datetime.fromtimestamp(value)


class UserSchema(Schema):
    id = fields.Int()
    email = fields.Email()
    # password = fields.Str()
    # active = fields.Boolean()
    online = fields.Boolean()
    last_activity = Timestamp()
    # created_at = Timestamp()


class RoomSchema(Schema):
    id = fields.Int()
    creator_id = fields.Int()
    created_at = Timestamp()
    members_id = fields.List(fields.Int())
    private = fields.Boolean()


class MessageSchema(Schema):
    id = fields.Int(dump_only=True)
    creator_id = fields.Int(dump_only=True)
    room_id = fields.Int(required=True)
    msg_type = fields.Int(required=True)
    msg_body = fields.Str(required=True)
    created_at = Timestamp(dump_only=True)


class CreateRoomSchema(Schema):
    # private = fields.Boolean()
    members_id = fields.List(fields.Int())


class AuthSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))


class LoginSchema(AuthSchema):
    device_name = fields.Str(default="Unknown", missing="Unknown")
    device_info = fields.Dict(default={}, missing={})



