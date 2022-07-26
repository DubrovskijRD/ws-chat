from typing import Awaitable, Callable, Optional

from aiohttp.web import Request, StreamResponse, middleware
from dependency_injector import containers, providers, resources
from dependency_injector.resources import T
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from src.infra.notificator import Notificator
from src.data.user.repo import UserRepo
from src.data.frineds.repo import FriendsRepo
from src.core.usecase.auth.register import UseCase as RegisterUseCase
from src.core.usecase.auth.login import UseCase as LoginUseCase
from src.core.usecase.auth.reset_pass import UseCase as ResetPassUseCase
from src.core.usecase.auth.reset_pass_confirm import UseCase as ResetPassConfirmUseCase
from src.application.handlers.websocket import query, connection, command


THandler = Callable[..., Awaitable[StreamResponse]]


class TestUseCase:
    def __init__(self, async_session):
        self.sess = async_session

    async def execute(self):
        result = await self.sess.execute("select 1")
        print("result: ", result.scalar())
        return


def db_engine(user, password, host, db_name):
    return create_async_engine(f'postgresql+asyncpg://{user}:{password}@{host}/{db_name}')


def session_factory(engine):
    return sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False
    )


class DbSessionResource(resources.Resource):

    def init(self, factory) -> Optional[T]:
        return factory()

    async def shutdown(self, session: Optional[T]) -> None:
        await session.close()


async def init_friend_repo(host, port, db_name, password):
    repo = FriendsRepo(host=host, port=port, db_name=db_name, auth=("neo4j", password))
    try:
        yield repo
    finally:
        await repo.close()


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    engine = providers.Singleton(
        db_engine,
        user=config.db_user,
        password=config.db_password,
        host=config.db_host,
        db_name=config.db_name
    )
    session_factory = providers.Singleton(
        sessionmaker,
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False
    )

    db_session = providers.Resource(
        DbSessionResource,
        factory=session_factory
    )

    notificator = providers.Factory(
        Notificator,
        email_sender=config.email_user,
        host="smtp.yandex.ru",
        user=config.email_user,
        password=config.email_password

    )

    test = providers.Factory(
        TestUseCase,
        async_session=db_session
    )

    user_repo = providers.Factory(
        UserRepo,
        db_session
    )
    friend_repo = providers.Resource(
        init_friend_repo,
        host=config.neo4j_host,
        port=config.neo4j_port,
        db_name=config.neo4j_db_name,
        password=config.neo4j_password
    )

    ws_connection_repo = providers.Singleton(
        dict
    )

    register_use_case = providers.Factory(
        RegisterUseCase,
        user_repo=user_repo,
        friend_repo=friend_repo,
        notificator=notificator
    )

    login_use_case = providers.Factory(
        LoginUseCase,
        user_repo=user_repo
    )

    reset_password_use_case = providers.Factory(
        ResetPassUseCase,
        user_repo=user_repo,
        notificator=notificator
    )

    reset_password_confirm_use_case = providers.Factory(
        ResetPassConfirmUseCase,
        user_repo=user_repo
    )

    # chat_repo = providers.Factory(
    #
    # )
    connect_handler = providers.Factory(
        connection.OnConnectHandler,
        friend_repo=friend_repo,
        user_repo=user_repo,
        ws_connection_repo=ws_connection_repo
    )

    disconnect_handler = providers.Factory(
        connection.OnDisconnectHandler,
        friend_repo=friend_repo,
        user_repo=user_repo,
        ws_connection_repo=ws_connection_repo
    )

    user_search_handler = providers.Factory(
        query.UserSearchQueryHandler,
        user_repo=user_repo,
        friend_repo=friend_repo,
    )

    friend_query_handler = providers.Factory(
        query.FriendQueryHandler,
        user_repo=user_repo,
        friend_repo=friend_repo

    )
    friend_request_query_handler = providers.Factory(
        query.FriendRequestQueryHandler,
        user_repo=user_repo,
        friend_repo=friend_repo
    )

    room_query_handler = providers.Factory(
        query.RoomQueryHandler,
        user_repo=user_repo,
        friend_repo=friend_repo
    )

    message_query_handler = providers.Factory(
        query.MessageQueryHandler,
        user_repo=user_repo
    )

    # COMMAND

    friend_command_handler = providers.Factory(
        command.FriendCommandHandler,
        friend_repo=friend_repo
    )

    room_command_handler = providers.Factory(
        command.RoomCommandHandler,
        user_repo=user_repo,
        friend_repo=friend_repo
    )
    message_command_handler = providers.Factory(
        command.MessageCommandHandler,
        user_repo=user_repo,
        friend_repo=friend_repo
    )


class ContainerContextWrapper:

    def __init__(self, container: Container):
        self.container = container

    async def __aenter__(self):
        return self.container

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
        # await self.container.db_session.shutdown()


def container_middleware(container: Container) -> THandler:

    context_container = ContainerContextWrapper(container)

    @middleware
    async def container_middleware_(
        request: Request,
        handler: THandler,
    ) -> StreamResponse:

        async with context_container as request['di']:
            return await handler(request)

    return container_middleware_
