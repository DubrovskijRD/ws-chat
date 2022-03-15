from weakref import WeakSet
from asyncio import Queue


class WebsocketSession:
    def __init__(self, ws, user_id, sid):
        self.sid = sid
        self.ws = ws
        self.user_id = user_id

    async def close(self, code, message):
        await self.ws.close(code=code, message=message)


class WsClient:
    def __init__(self, user_id):
        self.user_id = user_id
        self.session_list: WeakSet[WebsocketSession] = WeakSet()

    def add(self, session):
        self.session_list.add(session)

    def discard(self, session):
        self.session_list.discard(session)

    async def send_json(self, data):
        for session in self.session_list:
            try:
                await session.ws.send_json(data)
            except ConnectionResetError:
                pass

    @property
    def online(self):
        return bool(self.session_list)

    def __repr__(self):
        return f"<WsClient-{self.user_id}:{len(self.session_list)}:online={self.online}"

