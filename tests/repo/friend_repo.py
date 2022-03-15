import asyncio
import aiohttp
from aioneo4j import Neo4j


from src.data.frineds.repo import FriendsRepo

# async def go():
#     async with Neo4j('http://localhost:7474/', auth=("neo4j", "test")) as neo4j:
#         # data = await neo4j.data()
#         # print(data)
#         # assert bool(data)
#         result = await neo4j.cypher("CREATE (ee:Person {name: 'Roma', from: 'Russia', kloutScore: 9999})")
#         print(result)
#
#



async def go():
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



   #  session = aiohttp.client.ClientSession()
   #  body = {
   #     "statements": [{
   #         "statement": "CREATE (n:Person $props) RETURN n",
   #         "parameters": {
   #             "props": {
   #                 "name": "Roma"
   #             }
   #         }
   #     }]
   # }
    # response = None
    # try:
    #     response = await session.request('POST', url, auth=auth, json=body)
    #     data = await response.json()
    # finally:
    #     if response is not None:
    #         await response.release()

    # await session.close()
    # print(data)
    # async with aiohttp.client.ClientSession() as session:
    #     async with session.request('POST', url, auth=auth,
    #                                # headers={"Content-Type": "application/json"},
    #                                json={
    #
    #                                    "statements": [{
    #                                        "statement": "CREATE (n:Person $props) RETURN n",
    #                                        "parameters": {
    #                                            "props": {
    #                                                "name": "Roma"
    #                                            }
    #                                        }
    #                                    }]
    #
    #                                }) as req:
    #         result = await req.json()
    #         print(result)
        # async with session.request('POST', result['commit'], auth=auth, json={}) as req:
        #     result = await req.json()
        #     print(result)

loop = asyncio.get_event_loop()
loop.run_until_complete(go())
loop.close()

