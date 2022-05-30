import pytest

from src.data.frineds.repo import FriendsRepo


@pytest.mark.asyncio
async def test_friends_repo():
    db_name = "neo4j"
    host = "localhost"
    port = 7474
    url = f'http://localhost:7474/db/{db_name}/tx/commit'
    auth = ("neo4j", "test")

    repo = FriendsRepo(host=host, port=port, db_name=db_name, auth=auth)
    res = await repo.create_constraint_node("user_id_unique", "User", "id")
    print(res)
    # res = await repo.create_constraint("person_id_unique_2", "Person", "id")
    # print(res)
    # for i in range(10, 20):
    #     res = await repo.create_user(i, name=f"test{i}")
    #     print(res)
    # res = await repo.create_user(200, name="test2")
    # print(res)
    res = await repo.get_users(user_id_list=[1,100,300])
    print(res)
    res = await repo.create_friendship(user_id=10, friend_id=1)
    print("cf:", res)
    res = await repo.get_users()
    print(res)
    print("_"*10)
    res = await repo.get_friends_id(10)
    print(res)
    res = await repo.get_friends_id(1)
    print(res)
    res = await repo.get_incoming_friend_request(1)
    print("+", res)
    res = await repo.get_incoming_friend_request(2)
    print(res)
    res = await repo.get_incoming_friend_request(10)
    print(res)
    res = await repo.get_outgoing_friend_request(1)
    print(res)
    res = await repo.get_outgoing_friend_request(2)
    print("+", res)
    res = await repo.get_outgoing_friend_request(10)
    print("+", res)
    res = await repo.get_outgoing_friend_request(19)
    print(res)
    await repo.close()


