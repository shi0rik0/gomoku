import logging
from dataclasses import asdict
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from gomoku.api_loader import load_api_routes
from gomoku.jwt import get_current_user
from gomoku.state.server_state import server_state

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

load_dotenv()

app = FastAPI(
    title="五子棋游戏服务器",
    description="五子棋游戏服务器",
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

api_router = load_api_routes(
    Path(__file__).parent / "api",
    project_root=Path(__file__).parent.parent,
    base_prefix="/api",
)
app.include_router(api_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error for {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=422, content={"detail": exc.errors(), "body": exc.body}
    )
