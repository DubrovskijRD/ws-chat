import logging
from typing import List
from enum import Enum
import aiohttp

from src.core.exceptions.base import StorageError


logger = logging.getLogger(__name__)


class SafeDict(dict):
    def __missing__(self, key):
        return '{' + key + '}'


ERRORS = {
    "Neo.ClientError.Statement.SyntaxError": "",
    "Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists": "",
    "Neo.ClientError.Schema.ConstraintAlreadyExists": "",
    "Neo.ClientError.Statement.TypeError": "",
    'Neo.ClientError.Schema.ConstraintValidationFailed': 'message - Node(0) already exists with label `User` and property `id` = 1'
}

# match (e)-[r]-(e2) DELETE r
# match (e) DELETE e


class Label(Enum):
    USER = "User"
    FRIENDSHIP = "Friendship"


class FriendsRepo:

    def __init__(self, host, port, db_name, auth):
        url = "http://{host}:{port}/db/{db_name}/tx/commit"
        self.session = aiohttp.client.ClientSession()
        self.url = url.format(host=host, db_name=db_name, port=port)

        if not isinstance(auth, aiohttp.helpers.BasicAuth):
            auth = aiohttp.helpers.BasicAuth(*auth)
        self.auth = auth

    async def create_user(self, user_id, **extra_props) -> bool:
        create_node_stmt = "CREATE (n:{label} $props) RETURN n"
        stmt = create_node_stmt.format(label=Label.USER.value)
        props = {"id": user_id}
        props.update(extra_props)
        body = {
            "statements": [{
                "statement": stmt,
                "parameters": {"props": props}
            }]
        }

        result = await self._request(body)
        if result['errors']:
            raise StorageError(str(result['errors']))
        # todo check if not exist
        return True

    async def get_users(self, user_id_list: List[int] = None) -> List[id]:
        column = "u"
        where_stmt = f"where {column}.id IN {user_id_list}" if user_id_list else ""
        stmt = "MATCH ({column}:{label}) {where_stmt} RETURN {column}"
        stmt = stmt.format(label=Label.USER.value, column=column, where_stmt=where_stmt)
        body = {
            "statements": [{
                "statement": stmt
            }]
        }
        result = await self._request(body)
        if not user_id_list:
            print(result)
        if result['errors']:
            raise StorageError(str(result['errors']))

        stmt_result = result['results'][0]
        r_user_id_list = []
        for row in stmt_result['data']:
            r_user_id_list.extend(u['id'] for u in row['row'])

        return r_user_id_list

    async def get_friends_id(self, user_id) -> List[int]:
        stmt = """
                match (e:{user_label} {{id: $user_id}})-[r:{friendship_label}]->(d:{user_label})
                where exists((d)-[:{friendship_label}]->(e))
                return d
                """
        parameters = {
            "user_id": user_id
        }
        stmt = stmt.format_map(
            dict(
                user_label=Label.USER.value,
                friendship_label=Label.FRIENDSHIP.value
            )
        )
        body = {
            "statements": [{
                "statement": stmt,
                "parameters": parameters

            }]
        }
        result = await self._request(body)
        if result['errors']:
            raise StorageError(str(result['errors']))
        stmt_result = result['results'][0]
        r_user_id_list = []
        for row in stmt_result['data']:
            r_user_id_list.extend(u['id'] for u in row['row'])
        return r_user_id_list

    async def get_incoming_friend_request(self, user_id) -> List[int]:
        stmt = """
        match (e:{user_label})-[r:{friendship_label}]->(d:{user_label} {{id: $user_id}})
        Where Not exists((d)-[:{friendship_label}]->(e))
        Return e
        """
        parameters = {
            "user_id": user_id
        }
        stmt = stmt.format_map(
            dict(
                user_label=Label.USER.value,
                friendship_label=Label.FRIENDSHIP.value
            )
        )
        body = {
            "statements": [{
                "statement": stmt,
                "parameters": parameters

            }]
        }
        result = await self._request(body)
        if result['errors']:
            raise StorageError(str(result['errors']))
        stmt_result = result['results'][0]
        r_user_id_list = []
        for row in stmt_result['data']:
            r_user_id_list.extend(u['id'] for u in row['row'])
        return r_user_id_list

    async def get_outgoing_friend_request(self, user_id) -> List[int]:
        stmt = """
                match (e:{user_label} {{id: $user_id}})-[r:{friendship_label}]->(d:{user_label})
                Where Not exists((d)-[:{friendship_label}]->(e))
                Return d
                """
        parameters = {
            "user_id": user_id
        }
        stmt = stmt.format_map(
            dict(
                user_label=Label.USER.value,
                friendship_label=Label.FRIENDSHIP.value
            )
        )
        body = {
            "statements": [{
                "statement": stmt,
                "parameters": parameters

            }]
        }
        result = await self._request(body)
        if result['errors']:
            raise StorageError(str(result['errors']))
        stmt_result = result['results'][0]
        r_user_id_list = []
        for row in stmt_result['data']:
            r_user_id_list.extend(u['id'] for u in row['row'])
        return r_user_id_list

    async def create_friendship(self, user_id, friend_id) -> bool:
        if user_id == friend_id:
            raise StorageError(f"Cant create friendship between {user_id} {friend_id}")
        stmt = """
        match (e:{user_label}) where not exists((e)-[:Friendship]->(:{user_label} {{id: $friend_id}})) and e.id=$user_id
        match (d:{user_label}) where d.id=$friend_id
        create (e)-[r:{friendship_label}]->(d)
        return r
        """
        parameters = {
            "user_id": user_id,
            "friend_id": friend_id,
        }
        stmt = stmt.format_map(
            dict(
                user_label=Label.USER.value,
                friendship_label=Label.FRIENDSHIP.value
            )
        )
        print(stmt)
        body = {
            "statements": [{
                "statement": stmt,
                "parameters": parameters

            }]
        }
        result = await self._request(body)
        if result['errors']:
            raise StorageError(str(result['errors']))

        # todo check result if not found and not create
        return result

    # duplicate logic from request_friend
    # def accept_request(self, user_id, friend_id) -> bool:
    #     return True

    async def delete_friendship(self, user_id, friend_id) -> bool:
        return True

    async def remove_friend(self, user_id, friend_id) -> bool:
        return True

    async def close(self):
        await self.session.close()

    async def create_constraint_node(self, name, label, prop_name):
        create_constraint_stmt = """
        create constraint {name} FOR (n:{label})
        REQUIRE n.{prop_name} IS UNIQUE 
        """
        stmt = create_constraint_stmt.format(name=name, label=label, prop_name=prop_name)
        body = {
            "statements": [{
                "statement": stmt
            }]
        }
        result = await self._request(body)
        return result
    #
    #  Enterprise
    # async def create_constraint_rel(self, name, label, prop_name):
    #     create_constraint_stmt = """
    #     create constraint {name} FOR (n:{label})
    #     REQUIRE n.{prop_name} IS UNIQUE
    #     """
    #     stmt = create_constraint_stmt.format(name=name, label=label, prop_name=prop_name)
    #     body = {
    #         "statements": [{
    #             "statement": stmt
    #         }]
    #     }
    #     result = await self._request(body)
    #     return result

    async def _request(self, body, method='POST'):
        logger.debug(body)
        response = None
        try:
            response = await self.session.request(method, self.url, auth=self.auth, json=body)
            data = await response.json()
            return data
        finally:
            if response is not None:
                await response.release()
