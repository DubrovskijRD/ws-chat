import asyncio
from functools import wraps

from src.application.db import metadata
from src.application.containers import Container
from src.data.user.repo import UserRepo, UserSearchSpec, DeviceSearchSpec


class Conf:
    ...


conf = Conf()

test_func_list = []
conf.USER_ID = 0
conf.DEVICE_NAME = "phone"
conf.DEVICE_INFO = {"os": "ios9"}
conf.DEVICE_TOKEN = "123123"


def test(func):
    test_func_list.append(func)
    return func


@test
async def test_create_user(di):
    repo = await di.user_repo()
    user_id = await repo.create_user("asdda", "asd")

    conf.USER_ID = user_id
    assert isinstance(user_id, int)
    await repo.commit()

    user_list = await repo.get_users(UserSearchSpec(id_list=[user_id]))
    print(user_list)


@test
async def test_create_user_device(di):
    repo = await di.user_repo()
    device_id = await repo.create_device(user_id=conf.USER_ID,
                                         name=conf.DEVICE_NAME,
                                         info=conf.DEVICE_INFO,
                                         token=conf.DEVICE_TOKEN)
    assert isinstance(device_id, int)
    device_list = await repo.get_devices(DeviceSearchSpec(user_id=conf.USER_ID))
    print(device_list)
    print("hello world")


async def main():

    di = Container()
    await di.init_resources()

    engine = di.engine()
    async with engine.begin() as connection:
        await connection.run_sync(metadata.drop_all)
        await connection.run_sync(metadata.create_all)
    try:
        for test_func in test_func_list:
            await test_func(di)
    except Exception as e:
        print("FAIL:")
        print(f"test: {test_func}")
        print(f"error: {type(e)} - {e}")

    await di.shutdown_resources()

    async with engine.begin() as connection:
        await connection.run_sync(metadata.drop_all)



if __name__ == "__main__":
    asyncio.run(main())

