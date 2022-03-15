import logging
from typing import Union
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.core.exceptions.base import NotUniqueError
from src.core.usecase.base import SuccessResultBase, FailResultBase, UseCaseBase
from src.core.entity.user import Confirmation


logger = logging.getLogger(__name__)


@dataclass
class SuccessResult(SuccessResultBase):
    ...


@dataclass
class FailResult(FailResultBase):
    code: int
    msg: str


class UseCase(UseCaseBase):
    SuccessResult = SuccessResult
    FailResult = FailResult

    def __init__(self, user_repo, friend_repo, notificator):
        self.user_repo = user_repo
        self.notificator = notificator
        self.friend_repo = friend_repo

    async def execute(self, email: str, password: str) -> Union[SuccessResult, FailResult]:
        try:
            user_id = await self.user_repo.create_user(email, password)
        except NotUniqueError as e:
            return FailResult(e.code, str(e))
        code = Confirmation.generate_code()
        confirmation_id = await self.user_repo.create_confirmation(
            user_id, type_="register", code=code,
            expires_at=(datetime.utcnow()+timedelta(days=1))
        )
        res = await self.friend_repo.create_user(user_id, email=email)
        print(res)
        await self.user_repo.commit()



        try:
            await self.notificator.send_email(to=email, subject="Welcome! Thank's for register:)",
                                              text=f"This is your confirmation code: {code}")
        except Exception:
            logger.exception("notify error")

        return SuccessResult()

