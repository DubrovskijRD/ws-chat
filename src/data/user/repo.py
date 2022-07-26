from typing import Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime

import asyncpg
from sqlalchemy import update, select
from sqlalchemy.dialects.postgresql.asyncpg import AsyncAdapt_asyncpg_dbapi
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from src.core.exceptions.base import NotUniqueError, NotFoundError
from src.core.entity.user import User, Device, Confirmation, Room, Message
from src.data.user.models import UserModel, DeviceModel, ConfirmationModel, RoomModel, MessageModel, RoomMemberModel


def db_to_user(user_db: UserModel) -> User:
    return User(
        id=user_db.id,
        email=user_db.email,
        active=user_db.active,
        last_activity=user_db.last_activity,
        password=user_db.password,
        created_at=user_db.created_at,
        online=user_db.online
    )


def db_to_device(device_db: DeviceModel) -> Device:
    return Device(
        id=device_db.id,
        user_id=device_db.user_id,
        name=device_db.name,
        token=device_db.token,
        info=device_db.info,
        created_at=device_db.created_at
    )


def db_to_confirmation(confirmation_db: ConfirmationModel) -> Confirmation:
    return Confirmation(
        id=confirmation_db.id,
        user_id=confirmation_db.user_id,
        code=confirmation_db.code,
        expires_at=confirmation_db.expires_at,
        created_at=confirmation_db.created_at,
        type_=confirmation_db.type_,
        confirmed_at=confirmation_db.confirmed_at
    )


def db_to_room(room_db: RoomModel) -> Room:
    return Room(
        id=room_db.id,
        creator_id=room_db.creator_id,
        created_at=room_db.created_at,
        members_id=[member.user_id for member in room_db.members]
    )


def db_to_message(message_db: MessageModel) -> Message:
    return Message(
        id=message_db.id,
        room_id=message_db.room_id,
        creator_id=message_db.creator_id,
        msg_type=message_db.msg_type,
        msg_body=message_db.msg_body,
        created_at=message_db.created_at
    )


@dataclass
class UserSearchSpec:
    id_list: Optional[List[int]] = None
    email: Optional[str] = None
    email_like: Optional[str] = None
    token: Optional[str] = None

    def __repr__(self):
        spec_data = {k: v for k, v in asdict(self).items() if v}
        return f"UserSearchSpec({spec_data})"


@dataclass
class DeviceSearchSpec:
    id_list: Optional[List[int]] = None
    user_id: Optional[int] = None
    token: Optional[str] = None


@dataclass
class ConfirmationSearchSpec:
    id_list: Optional[List[int]] = None
    code: Optional[str] = None


@dataclass
class RoomSearchSpec:
    id_list: Optional[List[int]] = None
    member_id: Optional[int] = None  # user_id


@dataclass
class MessageSearchSpec:
    room_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    message_body_like: Optional[str] = None
    message_id: Optional[int] = None


class UserRepo:
    UserSearchSpec = UserSearchSpec
    DeviceSearchSpec = DeviceSearchSpec
    ConfirmationSearchSpec = ConfirmationSearchSpec
    RoomSearchSpec = RoomSearchSpec
    MessageSearchSpec = MessageSearchSpec

    def __init__(self, session):
        self.session = session

    async def get_users(self, spec: UserSearchSpec, exclude: Optional[UserSearchSpec] = None) -> List[User]:

        stmt = select(UserModel)
        if spec.id_list:
            stmt = stmt.where(UserModel.id.in_(spec.id_list))
        if spec.email:
            stmt = stmt.where(UserModel.email == spec.email)
        if spec.email_like:
            stmt = stmt.where(UserModel.email.like(f"%{spec.email_like}%"))
        if spec.token:
            stmt = stmt.join(DeviceModel).where(DeviceModel.token == spec.token)

        if exclude and exclude.id_list:
            stmt = stmt.where(UserModel.id.notin_(exclude.id_list))

        result = await self.session.execute(stmt)
        return [
            db_to_user(entity)
            for entity in result.scalars()
        ]

    async def create_user(self, email: str, password: str) -> int:
        user_db = UserModel(email=email, password=password)
        self.session.add(user_db)
        try:
            await self.session.flush()
        except IntegrityError as e:
            raise NotUniqueError(f"user not unique: {email}")
        return user_db.id

    async def update_user(self, user_id: int, data: dict):
        data = {k: v for k, v in data.items() if k in ['online', 'last_activity', 'active', 'password']}
        if not data:
            return False

        stmt = update(UserModel).where(UserModel.id == user_id).values(**data)
        res = await self.session.execute(stmt)
        return True

    async def create_device(self, user_id: int, name: str, info: dict, token: str):
        device_db = DeviceModel(
            user_id=user_id,
            name=name,
            info=info,
            token=token
        )
        self.session.add(device_db)
        try:
            await self.session.flush()
        except IntegrityError as e:
            raise NotUniqueError(f"device not unique: {name}")
        return device_db.id

    async def get_devices(self, spec: DeviceSearchSpec):
        stmt = select(DeviceModel)
        if spec.token:
            stmt = stmt.where(DeviceModel.token == spec.token)
        result = await self.session.execute(stmt)
        return [
            db_to_device(entity)
            for entity in result.scalars()
        ]

    async def create_confirmation(self, user_id: int, code: str, type_: str, expires_at: int):
        confirmation_db = ConfirmationModel(
            user_id=user_id,
            code=code,
            type_=type_,
            expires_at=expires_at
        )
        self.session.add(confirmation_db)
        try:
            await self.session.flush()
        except IntegrityError as e:
            print(e.orig)
            raise NotUniqueError(f"device not unique: {code}")
        return confirmation_db.id

    async def update_confirmation(self, confirmation_id: int, data: dict):
        data = {k: v for k, v in data.items() if k in ['confirmed_at']}
        if not data:
            return False
        stmt = update(ConfirmationModel).where(ConfirmationModel.id == confirmation_id).values(**data)
        res = await self.session.execute(stmt)
        return True

    async def get_confirmations(self, spec: ConfirmationSearchSpec = ConfirmationSearchSpec()):
        stmt = select(ConfirmationModel)
        # if spec.id_list:
        #     stmt = stmt.where(UserModel.id.in_(spec.id_list))
        # if spec.email_like:
        #     stmt = stmt.where(UserModel.email.like(spec.email_like))
        if spec.code:
            stmt = stmt.where(ConfirmationModel.code == spec.code)
        result = await self.session.execute(stmt)
        return [
            db_to_confirmation(entity)
            for entity in result.scalars()
        ]

    async def get_rooms(self, spec: RoomSearchSpec):
        stmt = select(RoomModel).options(selectinload(RoomModel.members))
        if spec.id_list:
            stmt = stmt.where(RoomModel.id.in_(spec.id_list))
        if spec.member_id:
            stmt = stmt.join(RoomMemberModel).where(RoomMemberModel.user_id == spec.member_id)
        # stmt = stmt.distinct()
        result = await self.session.execute(stmt)

        return [
            db_to_room(entity)
            for entity in result.scalars()
        ]

    async def create_room(self, creator_id: int, members_id: List[int], private=False):
        members = [RoomMemberModel(user_id=user_id) for user_id in members_id]
        room_db = RoomModel(creator_id=creator_id, private=private,
                            members=members)
        self.session.add(room_db)
        try:
            await self.session.flush()
        except IntegrityError as e:
            await self.session.rollback()
            if isinstance(e.orig, AsyncAdapt_asyncpg_dbapi.IntegrityError):
                raise NotFoundError(f"Not found users with {members_id=}") from e
            raise NotUniqueError(f"room not unique: {room_db}") from e
        return room_db.id

    async def get_messages(self, spec: MessageSearchSpec):
        stmt = select(MessageModel)
        if spec.message_id:
            stmt = stmt.where(MessageModel.id == spec.message_id)
        if spec.room_id:
            stmt = stmt.where(MessageModel.room_id == spec.room_id)
        if spec.start_time:
            stmt = stmt.where(MessageModel.created_at >= spec.start_time)
        if spec.end_time:
            stmt = stmt.where(MessageModel.created_at <= spec.end_time)
        result = await self.session.execute(stmt)

        return [
            db_to_message(entity)
            for entity in result.scalars()
        ]

    async def create_message(self, creator_id: int, room_id: int, msg_type: str, msg_body: str):
        message_db = MessageModel(
            room_id=room_id,
            creator_id=creator_id,
            msg_type=msg_type,
            msg_body=msg_body
        )
        self.session.add(message_db)
        try:
            await self.session.flush()
        except IntegrityError as e:
            await self.session.rollback()
            raise NotFoundError(obj="Room", search_spec={"room_id":room_id})
        return message_db.id

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()

