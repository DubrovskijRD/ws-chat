from typing import Union
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.core.exceptions.base import NotFoundError
from src.core.usecase.base import SuccessResultBase, FailResultBase, UseCaseBase
from src.core.entity.user import Confirmation


CONFIRM_RESET_PASSWORD_URL = 'http://seaborgix.ru/reset_pass_confirm/'


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

    def __init__(self, user_repo, notificator):
        self.user_repo = user_repo
        self.notificator = notificator

    async def execute(self, email: str,) -> Union[SuccessResult, FailResult]:
        try:
            spec = self.user_repo.UserSearchSpec(email=email)
            user_list = await self.user_repo.get_users(spec=spec)
        except NotFoundError as e:
            return FailResult(code=e.code, msg=str(e))
        if not user_list:
            return FailResult(code=NotFoundError.code, msg=NotFoundError.error_msg("user", spec))

        user = user_list[0]
        code = Confirmation.generate_code()
        try:
            confirmation_id = await self.user_repo.create_confirmation(
                user.id, type_="reset_password", code=code,
                expires_at=(datetime.utcnow() + timedelta(days=1))
            )
            html = f"""
            <html>
              <head></head>
              <body>
                <p>Запрос на смену пароля!<br>
                   Для смены пароля, перейдите по ссылке:<br>
                   <a href={CONFIRM_RESET_PASSWORD_URL + code}>{CONFIRM_RESET_PASSWORD_URL + code}</a>.
                </p>
                <small>Если вы не запрашивали смену пароля, это письмо следует проигнорировать</small>
              </body>
            </html>
            """
            await self.notificator.send_email(to=email, subject="Reset password!",
                                              text=html, textType="html")
        except Exception as e:
            await self.user_repo.rollback()
            return FailResult(msg="Unexpected error", code=6)
        return SuccessResult()

