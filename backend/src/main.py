import os
import uuid
from typing import List

from database import async_engine, get_async_connection, init_db, shutdown_db
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from jwt import create_token, get_current_user
from models import metadata, users_table
from schemas import UserCreate, UserResponse, UserUpdate
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql import delete, insert, select, update
from state import PlayerState, PlayerStatus, RoomState, server_state

load_dotenv()

app = FastAPI(
    title="FastAPI SQLAlchemy Core Async Demo",
    description="A demo application using FastAPI with SQLAlchemy Core and asyncpg.",
    version="1.0.0",
)


# 應用啟動事件處理
@app.on_event("startup")
async def startup_event():
    print("Application starting up...")
    # 初始化數據庫，創建表
    await init_db(metadata)
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
    room_id = str(uuid.uuid4())
    server_state.rooms[room_id] = RoomState(
        id=room_id, players=[current_user], host=current_user, ready=[False]
    )
    return {"room_id": room_id}


@app.post("/lobby/join-room")
async def join_room(current_user: str = Depends(get_current_user)):
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
