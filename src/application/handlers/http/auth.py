from aiohttp import web
from datetime import datetime
from dataclasses import asdict
from marshmallow import ValidationError
from aiohttp_cors import CorsViewMixin
from src.application.helpers import hash_password
from src.core.entity.user import User
from src.application.adapters import AuthSchema, LoginSchema, ResetPasswordSchema, ResetPasswordConfirmSchema


class RegisterView(web.View, CorsViewMixin):
    async def post(self):
        data = await self.request.json()
        schema = AuthSchema()
        try:
            data = schema.load(data)
        except ValidationError as e:
            return web.json_response({"status": "fail", "msg": e.normalized_messages()})
        data['password'] = hash_password(password=data['password'], salt=self.request.app['salt'])
        di = self.request['di']
        use_case = await di.register_use_case()
        result = await use_case.execute(data['email'], data['password'])
        if isinstance(result, use_case.SuccessResult):
            return web.json_response({"status": "success"})
        return web.json_response({"status": "fail", "error": asdict(result)})


class ConfirmationView(web.View, CorsViewMixin):
    async def get(self):
        confirm_code = self.request.query.get("code")
        if not confirm_code:
            return web.json_response({"status": "fail"})
        di = self.request['di']
        user_repo = di.user_repo()
        confirmation_list = await user_repo.get_confirmations(spec=user_repo.ConfirmationSearchSpec(code=confirm_code))
        try:
            confirmation = confirmation_list[0]
        except IndexError:
            return web.json_response({"status": "fail", "error": {"Not found": "неверный код подвтерждения"}})
        if confirmation.type_ != 'register':
            return web.json_response({"status": "fail", "error": {"Not found": "неверный код подвтерждения"}})
        if not confirmation.confirm():
            return web.json_response({"status": "fail"})
        await user_repo.update_confirmation(confirmation_id=confirmation.id, data=asdict(confirmation))
        res = await user_repo.update_user(user_id=confirmation.user_id, data=User.update(active=True))
        if not res:
            return web.json_response({"status": "fail"})
        await user_repo.commit()
        return web.json_response({"status": "success"})


class LoginView(web.View, CorsViewMixin):

    async def post(self):
        # todo try except json.decoder.JSONDecodeError
        data = await self.request.json()
        schema = LoginSchema()
        try:
            data = schema.load(data)
        except ValidationError as e:
            return web.json_response({"status": "fail", "error": e.normalized_messages()})
        data['password'] = hash_password(password=data['password'], salt=self.request.app['salt'])
        di = self.request['di']
        use_case = di.login_use_case()
        result = await use_case.execute(data['email'], data['password'], data['device_name'], data['device_info'])
        if isinstance(result, use_case.SuccessResult):
            return web.json_response({"status": "success", "data": asdict(result)})
        return web.json_response({"status": "fail", "error": asdict(result)})


class ResetPasswordView(web.View, CorsViewMixin):

    async def post(self):
        data = await self.request.json()
        schema = ResetPasswordSchema()
        try:
            data = schema.load(data)
        except ValidationError as e:
            return web.json_response({"status": "fail", "error": e.normalized_messages()})
        di = self.request['di']
        use_case = di.reset_password_use_case()
        result = await use_case.execute(data['email'])
        if isinstance(result, use_case.SuccessResult):
            return web.json_response({"status": "success", "data": asdict(result)})
        return web.json_response({"status": "fail", "error": asdict(result)})


class ResetPasswordConfirmView(web.View, CorsViewMixin):

    async def post(self):
        data = await self.request.json()
        schema = ResetPasswordConfirmSchema()
        try:
            data = schema.load(data)
        except ValidationError as e:
            return web.json_response({"status": "fail", "error": e.normalized_messages()})
        data['password'] = hash_password(password=data['password'], salt=self.request.app['salt'])
        di = self.request['di']
        use_case = di.reset_password_confirm_use_case()
        result = await use_case.execute(data['confirm_code'], data['password'])
        if isinstance(result, use_case.SuccessResult):
            return web.json_response({"status": "success", "data": asdict(result)})
        return web.json_response({"status": "fail", "error": asdict(result)})

