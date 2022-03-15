from dataclasses import dataclass, MISSING, asdict
from uuid import uuid4
from datetime import datetime
from typing import List

from src.core.exceptions.base import ValidationError


@dataclass
class User:
    id: int
    email: str
    password: str
    active: bool
    online: bool
    last_activity: datetime
    created_at: datetime

    def check_password(self, password: str):
        if self.password != password:
            raise ValidationError("Invalid password")
        return True

    @classmethod
    def update(cls, email: str = MISSING, password: str = MISSING, active: bool = MISSING,
               online: bool = MISSING,
               last_activity: datetime = MISSING):

        user_data = cls(email=email,
                        password=password,
                        active=active,
                        online=online,
                        last_activity=last_activity,
                        created_at=MISSING,
                        id=MISSING)

        d = asdict(user_data)

        return {k: v for k, v in d.items() if not isinstance(v, type(MISSING))}


@dataclass
class Device:
    id: int
    user_id: int
    name: str
    info: dict
    token: str
    created_at: datetime

    @staticmethod
    def generate_token():
        return str(uuid4())


@dataclass
class Confirmation:
    id: int
    user_id: int
    code: str
    type_: str
    confirmed_at: datetime
    created_at: datetime
    expires_at: datetime

    @property
    def is_confirmed(self):
        return bool(self.confirmed_at)

    @staticmethod
    def generate_code():
        return str(uuid4())

    def confirm(self):
        now = datetime.now()
        if self.expires_at < now:
            return False
        if self.is_confirmed:
            return False
        self.confirmed_at = now
        return True


@dataclass
class Room:
    id: int
    creator_id: int
    created_at: datetime
    members_id: List[int]
    private: bool = True

    @property
    def name(self):
        return f"room{self.id}"


@dataclass
class Message:
    id: int
    room_id: int
    creator_id: int
    msg_type: int
    msg_body: str
    created_at: datetime

    # todo msg_type Enum?
