import asyncio
import os

from src.application.db import metadata
from src.application.containers import Container
from src.data.user.repo import UserRepo, UserSearchSpec, DeviceSearchSpec


class Conf:
    ...


conf = Conf()

test_func_list = []
conf.USER_ID = 0
conf.USER_EMAIL = "romik8jones@gmail.com"
conf.DEVICE_NAME = "phone"
conf.DEVICE_INFO = {"os": "ios9"}
conf.DEVICE_TOKEN = "123123"


def test(func):
    test_func_list.append(func)
    return func


@test
async def test_register(di):
    uc = await di.register_use_case()

    result = await uc.execute(conf.USER_EMAIL, password="1234")
    print(result)
    repo = await di.user_repo()
    user_list = await repo.get_users(UserSearchSpec(id_list=[]))
    print(user_list)
    confirm_list = await repo.get_confirmations()
    print(confirm_list)


@test
async def test_login(di):
    uc = await di.login_use_case()

    result = await uc.execute(conf.USER_EMAIL, password="1234", device_name="test_device")
    print(result)


async def main():

    di = Container()
    di.config.from_dict({"email_user": "romik8jones@gmail.com", "email_password": os.getenv("EMAIL_PASS")})
    await di.init_resources()

    engine = di.engine()
    async with engine.begin() as connection:
        await connection.run_sync(metadata.drop_all)
        await connection.run_sync(metadata.create_all)
    try:
        for test_func in test_func_list:
            print(f"START {test_func.__name__}")
            await test_func(di)
            print(f"END {test_func.__name__}")
    except Exception as e:
        print("FAIL:")
        print(f"test: {test_func}")
        print(f"error: {type(e)} - {e}")

    await di.shutdown_resources()

    # async with engine.begin() as connection:
    #     await connection.run_sync(metadata.drop_all)



if __name__ == "__main__":
    asyncio.run(main())

