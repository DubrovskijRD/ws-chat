# ws-chat
simple chat on websockets - aiohttp, sqlalchemy, neo4j
frontend - https://github.com/DubrovskijRD/ws-chat-front


###Goals:

- get experience with: 
   - async SQLAlchemy ✔️
   - websocket ✔️
   - Neo4j ✔️
   - async dependency_injector ✔
   -  pytest-asyncio


*run:*
```commandline
docker build -t ws-chat .
docker run --env-file ./.env -p 8080:8080 ws-chat
```

*.env example:*
```
DB_USER=db_user
DB_PASS=db_pass
DB_HOST=db_host
DB_NAME=db_name
EMAIL_PASS=email_pass
SALT=salt123salt
NEO4J_PASS=neo4j_pass
```