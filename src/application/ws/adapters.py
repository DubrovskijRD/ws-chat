from enum import Enum
from marshmallow import Schema, fields, validate, post_load


class BaseSchema(Schema):
    # class Meta:
    #     unknown = INCLUDE
    ...


class WsMessageSchema(BaseSchema):
    resource = fields.Str(required=True)
    action = fields.Str(required=True, validate=validate.OneOf(['get', 'post', 'patch', 'delete']))
    payload = fields.Dict()


class QuerySchema(BaseSchema):
    resource = fields.Str(required=True)
    payload = fields.Dict()
    uid = fields.Str()


class CommandAction(Enum):
    CREATE = 'create'
    UPDATE = 'update'
    DELETE = 'delete'


class CommandSchema(BaseSchema):
    resource = fields.Str(required=True)
    payload = fields.Dict(required=True)
    action = fields.Str(required=True)

    @post_load
    def init_action(self, in_data, **kwargs):
        in_data['action'] = CommandAction(in_data['action'])
        return in_data
