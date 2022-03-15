from typing import Union
from dataclasses import dataclass

from src.core.exceptions.base import NotFoundError
from src.core.usecase.base import SuccessResultBase, FailResultBase, UseCaseBase


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

    def __init__(self, user_repo):
        self.user_repo = user_repo

    def execute(self, user_session) -> Union[SuccessResult, FailResult]:
        try:
            device = self.user_repo.get_device(user_session)
        except NotFoundError as e:
            return FailResult(4, msg="Unauthorized")

        self.user_repo.delete_device(device)
        self.user_repo.commit()
        return SuccessResult()
