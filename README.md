# ws-chat
simple chat on websockets - aiohtt, sqlalchemy, neo4j
frontend - https://github.com/DubrovskijRD/ws-chat-front


*run:*
```commandline
docker build -t ws-chat .
docker run --env-file ./.env -p 8080:8080 ws-chat
```