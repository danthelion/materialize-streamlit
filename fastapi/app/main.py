import asyncio
import os
from typing import List

import databases
import psycopg2
import sqlalchemy
from fastapi import FastAPI
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import create_engine

MESSAGE_STREAM_DELAY = 2  # seconds
MESSAGE_STREAM_RETRY_TIMEOUT = 15000  # miliseconds
# Materialize connection
DB_URL = os.getenv(
    "DATABASE_URL", "postgresql://materialize:materialize@localhost:6875/materialize"
)

database = databases.Database(DB_URL)
metadata = sqlalchemy.MetaData()
engine = create_engine(DB_URL)

# Convert numbers from postgres to floats instead of Decimal so that we can use serialize them as jsons with the
# defautl Python serializer
DEC2FLOAT = psycopg2.extensions.new_type(
    psycopg2.extensions.DECIMAL.values,
    "DEC2FLOAT",
    lambda value, curs: float(value) if value is not None else None,
)
psycopg2.extensions.register_type(DEC2FLOAT)

app = FastAPI()


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)


manager = ConnectionManager()


def new_messages():
    results = engine.execute("SELECT count(*) FROM sensors_view_1s")
    return None if results.fetchone()[0] == 0 else True


async def event_generator():
    if new_messages():
        connection = engine.raw_connection()
        with connection.cursor() as cur:
            cur.execute("DECLARE c CURSOR FOR TAIL sensors_view_1s")
            cur.execute("FETCH ALL c")
            for row in cur:
                yield row

    await asyncio.sleep(MESSAGE_STREAM_DELAY)


@app.websocket("/airquality")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            async for data in event_generator():
                await websocket.send_json(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
