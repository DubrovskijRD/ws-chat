import sqlalchemy as sa
from sqlalchemy.orm import relationship
from src.application.db import Base

from src.core.consts import RoomMessageType


class UserModel(Base):
    __tablename__ = 'user'

    id = sa.Column(sa.Integer, primary_key=True)
    email = sa.Column(sa.Text, unique=True, nullable=False)
    password = sa.Column(sa.Text, nullable=False)
    active = sa.Column(sa.Boolean, server_default='f', nullable=False)
    online = sa.Column(sa.Boolean, server_default='f', nullable=False)
    last_activity = sa.Column(sa.TIMESTAMP, server_default=sa.func.now(), nullable=False)
    created_at = sa.Column(sa.TIMESTAMP, server_default=sa.func.now(), nullable=False)


class ConfirmationModel(Base):
    __tablename__ = 'confirmation'

    id = sa.Column(sa.Integer, primary_key=True)
    code = sa.Column(sa.Text, nullable=False)
    # short_code = sa.Column(sa.Text, nullable=False)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'), nullable=False)
    type_ = sa.Column(sa.Text, nullable=False)
    confirmed_at = sa.Column(sa.TIMESTAMP, nullable=True)
    expires_at = sa.Column(sa.TIMESTAMP, nullable=False)
    created_at = sa.Column(sa.TIMESTAMP, server_default=sa.func.now(), nullable=False)


class DeviceModel(Base):
    __tablename__ = 'user_device'

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'), nullable=False)
    name = sa.Column(sa.Text, nullable=False)
    info = sa.Column(sa.JSON)
    token = sa.Column(sa.Text, unique=True)
    created_at = sa.Column(sa.TIMESTAMP, server_default=sa.func.now(), nullable=False)


class RoomMemberModel(Base):
    __tablename__ = 'room_member'
    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'), nullable=False)
    room_id = sa.Column(sa.Integer, sa.ForeignKey('room.id'), nullable=False)
    joined_at = sa.Column(sa.Date, server_default=sa.func.now(), nullable=False)

    __table_args__ = (sa.UniqueConstraint("user_id", "room_id"),)


# Chat #

class RoomModel(Base):
    __tablename__ = 'room'

    id = sa.Column(sa.Integer, primary_key=True)
    private = sa.Column(sa.Boolean, nullable=False, server_default='t')
    creator_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    created_at = sa.Column(sa.TIMESTAMP, server_default=sa.func.now(), nullable=False)
    members = relationship("RoomMemberModel", lazy="select")
    # todo name

    def __repr__(self):
        return f"<RoomModel:{self.id}>"


class MessageModel(Base):
    __tablename__ = 'message'

    id = sa.Column(sa.Integer, primary_key=True)
    room_id = sa.Column(sa.Integer, sa.ForeignKey('room.id'))
    creator_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    msg_type = sa.Column(sa.Integer, server_default=str(RoomMessageType.DEFAULT.value))
    msg_body = sa.Column(sa.Text, nullable=False)
    created_at = sa.Column(sa.TIMESTAMP, server_default=sa.func.now(), nullable=False)
    # todo attachments
