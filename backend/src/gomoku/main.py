import logging
from typing import Literal

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from gomoku.api.auth import router as auth_router
from gomoku.api.room import router as room_router
from gomoku.api.sse.game import router as sse_game_router
from gomoku.api.sse.room import router as sse_room_router
from gomoku.jwt import get_current_user
from gomoku.state.server_state import server_state

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

# # 應用啟動事件處理
# @app.on_event("startup")
# async def startup_event():
#     print("Application starting up...")
#     # 初始化數據庫，創建表
#     # await init_db(metadata)
#     print("Application startup complete.")


# # 應用關閉事件處理
# @app.on_event("shutdown")
# async def shutdown_event():
#     print("Application shutting down...")
#     # 關閉數據庫引擎
#     await shutdown_db()
#     print("Application shutdown complete.")

app.include_router(room_router)
app.include_router(sse_room_router)
app.include_router(sse_game_router)
app.include_router(auth_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error for {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=422, content={"detail": exc.errors(), "body": exc.body}
    )


class GetPlayerStateResponse(BaseModel):
    status: Literal["idle", "in_room", "in_game"]
    room_id: str | None = None
    game_id: str | None = None


@app.post("/get-player-state")
async def get_player_state(player_id: str = Depends(get_current_user)):
    player_state = server_state.player_state.get(player_id)
    if player_state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Player state not found"
        )
    return {"player_state": player_state}


# @app.post("/lobby/renew-room-id")
# async def renew_room_id(room_id: str, player_id: str = Depends(get_current_user)):
#     await room_id_manager.renew_lease(room_id)
#     return {"message": "Room ID lease renewed"}


# async def room_event_generator(player_id: str, room_id: str):
#     async with room_state_managers_lock:
#         room_state_manager = room_state_managers.get(room_id)
#         if not room_state_manager:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND, detail="Room not found"
#             )
#     queue, state = await room_state_manager.subscribe(player_id)
#     yield {"type": "initial_state", "state": state.to_json()}
#     try:
#         while True:
#             event = await queue.get()
#             yield {"type": "update", "state": event.to_json()}
#     finally:
#         await room_state_manager.unsubscribe(player_id)
