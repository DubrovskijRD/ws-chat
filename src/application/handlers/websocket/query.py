from src.application.ws.base import WebsocketSession
from src.application.ws.event import Query
from src.application.ws.server import BaseQueryHandler
from src.application.adapters import UserSchema, RoomSchema, MessageSchema
from src.data.user.repo import UserRepo
from src.data.frineds.repo import FriendsRepo
from src.core.exceptions.base import ValidationError


class UserSearchQueryHandler(BaseQueryHandler):

    def __init__(self, user_repo: UserRepo):
        self.user_repo = user_repo

    async def handle(self, query: Query, session: WebsocketSession):
        user_search_spec = self.user_repo.UserSearchSpec(email_like=query.payload.get('q'),
                                                         id_list=query.payload.get('id_list'))
        user_list = await self.user_repo.get_users(user_search_spec)
        await session.ws.send_json({"response": UserSchema().dump(user_list, many=True), "query": query.to_dict()})


class FriendQueryHandler(BaseQueryHandler):

    def __init__(self, user_repo: UserRepo, friend_repo: FriendsRepo):
        self.user_repo = user_repo
        self.friend_repo = friend_repo

    async def handle(self, query: Query, session: WebsocketSession):
        friends_id = await self.friend_repo.get_friends_id(session.user_id)

        if friends_id:
            spec = self.user_repo.UserSearchSpec(id_list=friends_id)
            user_list = await self.user_repo.get_users(spec)
        else:
            user_list = []
        await session.ws.send_json({"response": UserSchema().dump(user_list, many=True), "query": query.to_dict()})


class FriendRequestQueryHandler(BaseQueryHandler):

    def __init__(self,  user_repo: UserRepo, friend_repo: FriendsRepo):
        self.user_repo = user_repo
        self.friend_repo = friend_repo

    async def handle(self, query: Query, session: WebsocketSession):
        response = {}
        if query.payload.get("incoming"):
            incoming_id = await self.friend_repo.get_incoming_friend_request(session.user_id)
            if incoming_id:
                spec = self.user_repo.UserSearchSpec(id_list=incoming_id)
                user_list = await self.user_repo.get_users(spec)
                response.update({"incoming": UserSchema().dump(user_list, many=True)})
        if query.payload.get("outgoing"):
            outgoing_id = await self.friend_repo.get_outgoing_friend_request(session.user_id)
            if outgoing_id:
                spec = self.user_repo.UserSearchSpec(id_list=outgoing_id)
                user_list = await self.user_repo.get_users(spec)
                response.update({"outgoing": UserSchema().dump(user_list, many=True)})
        await session.ws.send_json({"response": response, "query": query.to_dict()})


class RoomQueryHandler(BaseQueryHandler):
    def __init__(self, user_repo: UserRepo, friend_repo):
        self.user_repo = user_repo
        # self.friend_repo = friend_repo

    async def handle(self, query: Query, session: WebsocketSession):
        room_list = await self.user_repo.get_rooms(self.user_repo.RoomSearchSpec(member_id=session.user_id))
        await session.ws.send_json({"response": RoomSchema().dump(room_list, many=True), "query": query.to_dict()})


class MessageQueryHandler(BaseQueryHandler):
    def __init__(self, user_repo: UserRepo):
        self.user_repo = user_repo

    async def handle(self, query: Query, session: WebsocketSession):
        if not query.payload.get('room_id'):
            await session.ws.send_json(ValidationError("not found room_id in message query payload").to_dict())
        message_list = await self.user_repo.get_messages(
            spec=self.user_repo.MessageSearchSpec(room_id=query.payload['room_id'])
        )
        await session.ws.send_json({"response": MessageSchema().dump(message_list, many=True),
                                    "query": query.to_dict()})

