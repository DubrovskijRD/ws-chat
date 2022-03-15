import asyncio
import logging
import json
from typing import Dict, List, Callable, Optional, Any, Awaitable
from aiohttp import web, WSMsgType, WSCloseCode
from marshmallow import ValidationError

from src.core.exceptions.base import DomainError, NotFoundError, UnauthorizedError,\
    ValidationError as DomainValidationError
from src.application.ws.event import Command, Query, event_from_dict, Broadcast
from src.application.ws.base import WsClient, WebsocketSession


logger = logging.getLogger(__name__)


class BaseCommandHandler:
    async def __call__(self, command: Command, session: WebsocketSession) -> List[Broadcast]:
        command_action_name = command.action.value.lower()
        if hasattr(self, command_action_name):
            action_handler = getattr(self, command_action_name)
            return await action_handler(command, session)
        else:
            await session.ws.send_json(
                DomainValidationError(obj="command action", value="command_action_name").to_dict()
            )


class BaseQueryHandler:
    async def __call__(self, query: Query, session: WebsocketSession):
        await self.handle(query, session)

    async def handle(self, query: Query, session: WebsocketSession):
        raise NotImplementedError(f" Not implemented handle method for {type(self)}")


class WebSocketServer:

    def __init__(self, user_repo, ws_connection_repo: Dict[Any, WsClient]):
        self.user_repo = user_repo
        self.ws_clients = ws_connection_repo
        self.command_handlers: Dict[str, BaseCommandHandler] = {}
        self.query_handlers: Dict[str, BaseQueryHandler] = {}
        self.connect_handler = None
        self.disconnect_handler = None
        # self.disconnect_handler: Optional[Callable[[None, WebsocketSession], Awaitable[List[Broadcast]]]] = None

    async def handle(self, request):
        try:
            user = await self.get_user(request)
        except UnauthorizedError:
            return web.json_response({"status": "fail", "code": 2}, status=401)
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        client = self.ws_clients.setdefault(user.id, WsClient(user_id=user.id))
        session = WebsocketSession(ws=ws, user_id=user.id, sid=None)
        client.add(session)
        await self.on_connect(session)
        await self.handle_websocket(session)
        await self.on_disconnect(session)

        client.discard(ws)
        return ws

    async def handle_websocket(self, session):
        async for msg in session.ws:
            if msg.type == WSMsgType.TEXT:
                if msg.data == 'close':
                    await session.ws.close()
                    break
                else:
                    try:
                        event = event_from_dict(json.loads(msg.data))
                    except ValidationError as err:
                        await session.ws.send_json(DomainValidationError(msg=err.normalized_messages()).to_dict())
                    except DomainValidationError as err:
                        await session.ws.send_json(err.to_dict())
                    else:
                        stop = await self.handle_event(event, session)
                        if stop:
                            break

            elif msg.type == WSMsgType.ERROR:
                logger.debug('ws connection closed with exception %s' %
                      session.ws.exception())

    async def on_connect(self, session):
        if self.connect_handler:
            connect_handler = await self.connect_handler()
            broadcast_list = await connect_handler(None, session)
            logger.debug(f"{broadcast_list}, {len(broadcast_list)}")
            await asyncio.gather(*[self.broadcast(broadcast_message) for broadcast_message in broadcast_list])
        else:
            logger.debug(f"New connection: {session}")

    async def on_disconnect(self, session):
        if self.disconnect_handler:
            disconnect_handler = await self.disconnect_handler()
            broadcast_list = await disconnect_handler(None, session)
            logger.debug(f"{broadcast_list}, {len(broadcast_list)}")
            await asyncio.gather(*[self.broadcast(broadcast_message) for broadcast_message in broadcast_list])
        else:

            logger.debug(f"Connection close {session}")

    async def handle_event(self, event, session):
        try:
            logger.debug(f"{event} - {session}")
            if isinstance(event, Query):
                query_handler = self.query_handlers[event.resource]
                await query_handler(event, session)
            elif isinstance(event, Command):
                command_handler = self.command_handlers[event.resource]
                broadcast_list = await command_handler(event, session)
                logger.debug(f"broadcast: {broadcast_list}")
                await asyncio.gather(*[self.broadcast(broadcast_message) for broadcast_message in broadcast_list])

        except KeyError as e:
            try:
                await session.ws.send_json(DomainValidationError(f"Invalid resource {e}").to_dict())
            except ConnectionResetError:
                # connection already close
                return True

    async def broadcast(self, broadcast: Broadcast):
        for receiver in broadcast.receivers:
            client = self.ws_clients.get(receiver)
            if client:
                await client.send_json(broadcast.event.to_dict())

    async def get_user(self, request):
        session_token = request.headers.get("sid") or request.query.get('sid')
        if not session_token:
            raise UnauthorizedError()
        try:
            user_list = await self.user_repo.get_users(self.user_repo.UserSearchSpec(token=session_token))
        except NotFoundError:
            raise UnauthorizedError()
        except Exception:
            self.user_repo.rollback()
            raise
        if not user_list:
            raise UnauthorizedError()
        user = user_list[0]
        # todo: self.user_repo.update_device(spec=token, last_usage=datetime.now())
        return user

    async def shutdown(self):
        clients = list(self.ws_clients.values())
        logger.debug(f"shutdown clients: {clients}")
        for client in clients:
            for session in set(client.session_list):
                logger.debug(f"close: {session}")
                await session.close(code=WSCloseCode.GOING_AWAY,
                               message='Server shutdown')

    def register_command_handlers(self, handler_list):
        for resource, handler in handler_list:
            self.command_handlers[resource] = handler

    def register_query_handlers(self, handler_list):
        for resource, handler in handler_list:
            self.query_handlers[resource] = handler
