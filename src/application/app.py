import os
import logging
from typing import Callable
from dataclasses import dataclass, asdict

from aiohttp import web
import aiohttp_cors

from src.application.handlers.http import views as http_views
from src.application.handlers.websocket import connection
from src.application.containers import Container, container_middleware
from src.application.ws.server import WebSocketServer
from src.application.db import metadata


logging.basicConfig(level=logging.DEBUG)


async def index(request: web.Request) -> web.Response:
    # raise ValueError("asd")
    di = request['di']
    uc = await di.test()
    result = await uc.execute()

    return web.json_response(
        {
            "status": "ok", "data": str(result)
        },
    )


async def on_shutdown(app: web.Application):
    print("SHUTDOWN")
    await app.ws_server.shutdown()
    await app.container.shutdown_resources()


async def app_factory():
    container = Container()
    container.config.from_dict(
        dict(email_user="romik8jones@gmail.com",
             email_password=os.getenv("EMAIL_PASS"),
             db_user=os.getenv("DB_USER"),
             db_password=os.getenv("DB_PASS"),
             db_host=os.getenv("DB_HOST"),
             db_name=os.getenv("DB_NAME"),
             neo4j_host="localhost",
             neo4j_port=7474,
             neo4j_db_name="neo4j",
             neo4j_password=os.getenv("NEO4J_PASS"),
             )
    )

    # engine = container.engine()
    # async with engine.begin() as connection:
    #     # await connection.run_sync(metadata.drop_all)
    #     await connection.run_sync(metadata.create_all)

    app = web.Application(middlewares=[
        container_middleware(container)
    ])
    app.container = container
    ws_client_repo = dict()
    # ws_worker = WsWorker(user_repo=await container.user_repo(), friends_repo=FriendsRepo(),
    #                      ws_client_repo=ws_client_repo)
    ws_server = WebSocketServer(user_repo=container.user_repo(),
                                ws_connection_repo=container.ws_connection_repo())
    ws_server.register_command_handlers((
        ('friend', await container.friend_command_handler()),
        ('message', await container.message_command_handler()),
        ('room', await container.room_command_handler())
    ))
    ws_server.register_query_handlers((
        ('user', await container.user_search_handler()),
        ('friend', await container.friend_query_handler()),
        ('friend_request', await container.friend_request_query_handler()),
        ('room', await container.room_query_handler()),
        ('message', container.message_query_handler()),
    ))
    ws_server.connect_handler = container.connect_handler
    ws_server.disconnect_handler = container.disconnect_handler

    app.ws_server = ws_server
    app['salt'] = os.getenv("SALT")

    # await ahsa.init_db(app, metadata)

    app.add_routes([web.get('/connect', ws_server.handle)])
    for method, path, handler in http_views:
        app.router.add_route(method, path, handler)

    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })

    # Configure CORS on all routes.
    for route in list(app.router.routes()):
        cors.add(route)

    app.on_shutdown.append(on_shutdown)
    return app
