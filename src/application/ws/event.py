from typing import List, Union
from dataclasses import dataclass, field

from src.core.exceptions.base import ValidationError
from .adapters import QuerySchema, CommandSchema, CommandAction


class BaseWsEvent:
    _schema: Union[QuerySchema, CommandSchema]

    def to_dict(self):
        return self._schema.dump(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**cls._schema.load(data))


@dataclass
class Query(BaseWsEvent):

    resource: str
    payload: dict = None
    uid: str = "-"

    _schema = QuerySchema()


@dataclass
class Command(BaseWsEvent):
    resource: str
    action: CommandAction
    payload: dict
    uid: str = "-"

    _schema = CommandSchema()


def event_from_dict(data):
    try:
        type_ = data.pop('type')
        if type_ == 'query':
            return Query.from_dict(data)
        if type_ == 'command':
            return Command.from_dict(data)
        raise ValidationError(f"Invalid type {data['type']}")
    except KeyError:
        raise ValidationError("Invalid event format, missing 'type'")


class ServerEvent:
    ...

    def to_dict(self):
        raise NotImplementedError(f"to_dict not implemented for {type(self)}")


@dataclass
class QueryResponse(ServerEvent):
    query: Query
    data: dict

    def to_dict(self):
        return {"query": self.query.to_dict(), "data": self.data}


@dataclass
class CommandDoneEvent(ServerEvent):
    command: Command
    user_id: int
    result: dict = field(default_factory=dict)

    def to_dict(self):
        return {"command": self.command.to_dict(), "user_id": self.user_id, "result": self.result}


@dataclass
class Broadcast:
    receivers: List[int]
    event: ServerEvent


