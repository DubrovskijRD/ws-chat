from typing import List
from datetime import datetime
from src.application.ws.base import WebsocketSession
from src.application.ws.event import Broadcast, CommandDoneEvent, Command, CommandAction
from src.data.user.repo import UserRepo


class OnConnectHandler:
    def __init__(self, friend_repo, user_repo: UserRepo, ws_connection_repo):
        self.friend_repo = friend_repo
        self.user_repo = user_repo
        self.ws_connection_repo = ws_connection_repo

    async def __call__(self, _, session: WebsocketSession) -> List[Broadcast]:
        # client = self.ws_connection_repo.get(session.user_id)
        # todo duplicate online broadcasting
        # if len(client.session_list) > 1:
        #     pass
        online = True

        await self.user_repo.update_user(user_id=session.user_id, data={"online": online, "last_activity": datetime.now()})
        await self.user_repo.commit()

        friends_id = await self.friend_repo.get_friends_id(session.user_id)
        command = Command(resource='friends',
                          action=CommandAction.UPDATE,
                          payload={
                              "online": online,
                              "id": session.user_id
                          })
        if friends_id:
            return [Broadcast(
                receivers=friends_id,
                event=CommandDoneEvent(command=command, user_id=session.user_id)
            )]
        return []


class OnDisconnectHandler:
    def __init__(self, friend_repo, user_repo: UserRepo, ws_connection_repo):
        self.friend_repo = friend_repo
        self.user_repo = user_repo
        self.ws_connection_repo = ws_connection_repo

    async def __call__(self, _, session: WebsocketSession) -> List[Broadcast]:
        client = self.ws_connection_repo.get(session.user_id)

        if client:
            online = client.online
        else:
            online = False
        if online:
            return []

        await self.user_repo.update_user(user_id=session.user_id,
                                         data={"online": online, "last_activity": datetime.now()})
        await self.user_repo.commit()
        friends_id = await self.friend_repo.get_friends_id(session.user_id)
        command = Command(resource='friends',
                          action=CommandAction.UPDATE,
                          payload={
                              "online": online,
                              "id": session.user_id
                          })
        if friends_id:
            return [Broadcast(
                receivers=friends_id,
                event=CommandDoneEvent(command=command, user_id=session.user_id)
            )]
        return []

