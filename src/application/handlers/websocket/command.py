from typing import List
from marshmallow import ValidationError
from src.core.exceptions.base import ValidationError as DomainValidationError, NotFoundError
from src.application.ws.event import Command, Broadcast, CommandDoneEvent
from src.application.ws.base import WebsocketSession
from src.application.ws.server import BaseCommandHandler
from src.data.frineds.repo import FriendsRepo
from src.data.user.repo import UserRepo
from src.application.adapters import MessageSchema


class FriendCommandHandler(BaseCommandHandler):
    def __init__(self, friend_repo: FriendsRepo):
        self.friend_repo = friend_repo

    async def create(self, command: Command, session: WebsocketSession) -> List[Broadcast]:
        friend_id = command.payload.get('user_id')
        if not friend_id:
            session.ws.send_json(DomainValidationError("not found user_id in create friend payload").to_dict())
            return []
        user_id = session.user_id
        await self.friend_repo.create_friendship(user_id, friend_id)
        return [Broadcast(receivers=[friend_id, user_id], event=CommandDoneEvent(command=command, user_id=user_id))]


class RoomCommandHandler(BaseCommandHandler):
    def __init__(self, user_repo: UserRepo, friend_repo: FriendsRepo):
        self.friend_repo = friend_repo
        self.user_repo = user_repo

    async def create(self, command: Command, session: WebsocketSession) -> List[Broadcast]:
        members_id = command.payload.get('members_id')
        if not members_id:
            await session.ws.send_json(DomainValidationError("members_id: Missing").to_dict())
            return []
        try:
            members_id.append(session.user_id)
            members_id = list(set(members_id))
            room_id = await self.user_repo.create_room(creator_id=session.user_id, members_id=members_id,
                                                       private=command.payload.get('private', True))
        # todo NotFound, NotUnique
        except:
            raise
        await self.user_repo.commit()
        return [Broadcast(receivers=members_id,
                          event=CommandDoneEvent(command=command, user_id=session.user_id, result={"id": room_id}))]


class MessageCommandHandler(BaseCommandHandler):
    def __init__(self, user_repo: UserRepo, friend_repo: FriendsRepo):
        self.user_repo = user_repo
        self.friend_repo = friend_repo

    async def create(self, command: Command, session: WebsocketSession) -> List[Broadcast]:
        try:
            payload = MessageSchema().load(command.payload)
        except ValidationError as err:
            await session.ws.send_json(DomainValidationError(err.normalized_messages()).to_dict())
            return []
        spec = self.user_repo.RoomSearchSpec(id_list=[payload.get('room_id')])
        room_list = await self.user_repo.get_rooms(spec)
        try:
            room = room_list[0]
        except IndexError:
            session.ws.send_json(NotFoundError(obj="Room", search_spec=spec).to_dict())
            return []

        msg_id = await self.user_repo.create_message(creator_id=session.user_id,
                                                     room_id=payload['room_id'],
                                                     msg_type=payload['msg_type'],
                                                     msg_body=payload['msg_body'])
        await self.user_repo.commit()
        message_list = await self.user_repo.get_messages(self.user_repo.MessageSearchSpec(message_id=msg_id))
        return [Broadcast(receivers=room.members_id,
                          event=CommandDoneEvent(command=command, user_id=session.user_id, result=MessageSchema().dump(message_list, many=True)))]
