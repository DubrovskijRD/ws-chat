from typing import Union
from dataclasses import dataclass

from src.core.exceptions.base import NotFoundError
from src.core.usecase.base import SuccessResultBase, FailResultBase, UseCaseBase


@dataclass
class SuccessResult(SuccessResultBase):
    user: object


@dataclass
class FailResult(FailResultBase):
    code: int
    msg: str


class UseCase(UseCaseBase):
    SuccessResult = SuccessResult
    FailResult = FailResult

    def __init__(self, user_repo):
        self.user_repo = user_repo

    def execute(self, user_session) -> Union[SuccessResult, FailResult]:
        try:
            user = self.get_user_by_identification(user_session)
        except NotFoundError as e:
            return FailResult(code=5, msg="Unauthorized")
        if not user.active:
            return FailResult(code=3, msg="Forbidden")
        return SuccessResult(user)
