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

    def execute(self, confirm_code) -> Union[SuccessResult, FailResult]:
        try:
            confirmation = self.user_repo.get_confirmations(confirm_code)
        except NotFoundError as e:
            return FailResult(code=e.code, msg=str(e))
        if confirmation.expired():
            return FailResult(code=NotFoundError.code, msg="Not found confirmation")
        if confirmation.type_ != "email":
            return FailResult(code=NotFoundError.code, msg="Not found confirmation")

        user = self.user_repo.get_user(confirmation.user_id)
        user.activate()
        self.user_repo.update_user(user)
        self.user_repo.commit()
        return SuccessResult()
