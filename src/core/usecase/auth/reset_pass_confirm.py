from typing import Union
from dataclasses import dataclass, asdict

from src.core.exceptions.base import NotFoundError
from src.core.usecase.base import SuccessResultBase, FailResultBase, UseCaseBase
from src.core.entity.user import Confirmation, User


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

    async def execute(self, confirm_code: str, password: str) -> Union[SuccessResult, FailResult]:
        spec = self.user_repo.ConfirmationSearchSpec(code=confirm_code)
        confirmation_list = await self.user_repo.get_confirmations(
            spec=spec
        )
        try:
            confirmation = confirmation_list[0]
        except IndexError:
            return FailResult(msg=NotFoundError.error_msg(obj=Confirmation, spec=spec), code=NotFoundError.code)
        if confirmation.type_ != 'reset_password':
            return FailResult(msg=NotFoundError.error_msg(obj=Confirmation, spec=spec), code=NotFoundError.code)
        if not confirmation.confirm():
            return FailResult(msg=NotFoundError.error_msg(obj=Confirmation, spec=spec), code=NotFoundError.code)
        try:
            await self.user_repo.update_confirmation(confirmation_id=confirmation.id, data=asdict(confirmation))
            await self.user_repo.update_user(user_id=confirmation.user_id, data=User.update(password=password))
            await self.user_repo.commit()
        except Exception as e:
            await self.user_repo.rollback()
            return FailResult(msg="Unexpected error", code=6)
        return SuccessResult()
