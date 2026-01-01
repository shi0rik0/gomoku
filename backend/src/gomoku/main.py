import asyncio
import json
import logging
import os
import uuid
from typing import List

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql import delete, insert, select, update

from gomoku.database import async_engine, get_async_connection, init_db, shutdown_db
from gomoku.jwt import create_token, get_current_player_from_query, get_current_user
from gomoku.models import metadata, users_table
from gomoku.room_id_manager import room_id_manager
from gomoku.schemas import UserCreate, UserResponse, UserUpdate
from gomoku.state import (
    PlayerState,
    PlayerStatus,
    RoomState,
    room_state_managers,
    room_state_managers_lock,
    server_state,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

load_dotenv()

app = FastAPI(
    title="FastAPI SQLAlchemy Core Async Demo",
    description="A demo application using FastAPI with SQLAlchemy Core and asyncpg.",
    version="1.0.0",
)

# 开发环境允许所有来源的请求
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("Gomoku main module loaded.!!!!!!!!")


# 應用啟動事件處理
@app.on_event("startup")
async def startup_event():
    print("Application starting up...")
    # 初始化數據庫，創建表
    # await init_db(metadata)
    print("Application startup complete.")


# 應用關閉事件處理
@app.on_event("shutdown")
async def shutdown_event():
    print("Application shutting down...")
    # 關閉數據庫引擎
    await shutdown_db()
    print("Application shutdown complete.")


@app.get("/")
async def read_root():
    return {"message": "Welcome to FastAPI with SQLAlchemy Core Async!"}


@app.post("/auth/login-anonymous")
async def login_anonymous():
    user_id = str(uuid.uuid4())
    token = create_token(user_id)
    logger.info(f"Anonymous user logged in with ID: {user_id}")
    return {"access_token": token}


@app.post("/get-user-id")
async def get_user_id(current_user: str = Depends(get_current_user)):
    return {"user_id": current_user}


@app.post("/auth/verify-token")
async def verify_token_endpoint(current_user: str = Depends(get_current_user)):
    return {"user_id": current_user}


@app.post("/lobby/create-room")
async def create_room(current_user: str = Depends(get_current_user)):
    players = server_state.players
    if current_user not in players:
        players[current_user] = PlayerState(
            id=current_user, name="Anonymous", status=PlayerStatus.IN_ROOM
        )
    room_id = await room_id_manager.acquire_room_id()
    async with room_state_managers_lock:
        room_state_managers[room_id] = RoomState(
            RoomState(
                id=room_id,
                players=[current_user, None],
                host=current_user,
                ready=[True, False],
            )
        )
    return {"room_id": room_id}


@app.post("/lobby/join-room")
async def join_room(room_id: str, current_user: str = Depends(get_current_user)):
    players = server_state.players
    if current_user not in players:
        players[current_user] = PlayerState(
            id=current_user, name="Anonymous", status=PlayerStatus.IN_ROOM
        )


@app.post("/lobby/leave-room")
async def leave_room(current_user: str = Depends(get_current_user)):
    players = server_state.players
    if current_user not in players:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Player not found"
        )
    player_state = players[current_user]


@app.post("/lobby/set-ready")
async def set_ready(
    is_ready: bool, room_id: str, current_user: str = Depends(get_current_user)
):
    async with room_state_managers_lock:
        room_state_manager = room_state_managers.get(room_id)
        if not room_state_manager:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Room not found"
            )

    def update_player_ready(data: RoomState):
        if current_user not in data.players:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Player not in the room",
            )
        index = data.players.index(current_user)
        data.ready[index] = is_ready
        return data, data

    await room_state_manager.update(update_player_ready)
    return {"message": "Player ready status updated"}


@app.post("/lobby/renew-room-id")
async def renew_room_id(room_id: str, current_user: str = Depends(get_current_user)):
    await room_id_manager.renew_lease(room_id)
    return {"message": "Room ID lease renewed"}


async def event_generator(user_id: str):
    while True:
        await asyncio.sleep(5)
        yield {
            "msg": f"Hello, user {user_id}! The server time is {asyncio.get_event_loop().time()}"
        }


async def sse_event_generator(event_generator):
    async for event in event_generator:
        json_str = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
        yield f"data: {json_str}\n\n"


@app.get("/events")
async def get_events(current_player: str = Depends(get_current_player_from_query)):
    return StreamingResponse(
        sse_event_generator(event_generator(current_player)),
        media_type="text/event-stream",
    )


async def room_event_generator(player_id: str, room_id: str):
    async with room_state_managers_lock:
        room_state_manager = room_state_managers.get(room_id)
        if not room_state_manager:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Room not found"
            )
    queue, state = await room_state_manager.subscribe(player_id)
    yield {"type": "initial_state", "state": state.to_json()}
    try:
        while True:
            event = await queue.get()
            yield {"type": "update", "state": event.to_json()}
    finally:
        await room_state_manager.unsubscribe(player_id)


@app.get("/lobby/events")
async def lobby_events(
    player_id: str = Depends(get_current_player_from_query), room_id: str = Query(None)
):
    return StreamingResponse(
        sse_event_generator(room_event_generator(player_id, room_id)),
        media_type="text/event-stream",
    )
