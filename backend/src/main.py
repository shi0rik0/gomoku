import os
import uuid
from typing import List

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql import delete, insert, select, update

from database import async_engine, get_async_connection, init_db, shutdown_db
from jwt import create_token, get_current_user
from models import metadata, users_table
from schemas import UserCreate, UserResponse, UserUpdate

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


# 創建用戶
@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate, conn: AsyncConnection = Depends(get_async_connection)
):
    # 構建插入語句
    insert_stmt = (
        insert(users_table)
        .values(name=user.name, email=user.email, is_active=user.is_active)
        .returning(users_table)
    )  # 返回插入的行數據

    try:
        # 執行插入語句並獲取結果
        result = await conn.execute(insert_stmt)
        created_user = result.fetchone()  # 獲取插入的行

        if created_user is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user.",
            )
        return UserResponse.model_validate(created_user)  # Pydantic v2+
        # return UserResponse.from_orm(created_user) # Pydantic v1

    except Exception as e:
        # 處理唯一約束錯誤等
        if "duplicate key value violates unique constraint" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email '{user.email}' already exists.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}",
        )


# 獲取所有用戶
@app.get("/users/", response_model=List[UserResponse])
async def read_users(conn: AsyncConnection = Depends(get_async_connection)):
    # 構建查詢語句
    select_stmt = select(users_table).order_by(users_table.c.id)
    # 執行查詢
    result = await conn.execute(select_stmt)
    # 獲取所有行
    users = result.fetchall()
    return [UserResponse.model_validate(user) for user in users]  # Pydantic v2+
    # return [UserResponse.from_orm(user) for user in users] # Pydantic v1


# 獲取單個用戶
@app.get("/users/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: int, conn: AsyncConnection = Depends(get_async_connection)
):
    # 構建查詢語句
    select_stmt = select(users_table).where(users_table.c.id == user_id)
    # 執行查詢並獲取單行
    result = await conn.execute(select_stmt)
    user = result.fetchone()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return UserResponse.model_validate(user)  # Pydantic v2+
    # return UserResponse.from_orm(user) # Pydantic v1


# 更新用戶
@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    conn: AsyncConnection = Depends(get_async_connection),
):
    # 創建一個字典，只包含非 None 的更新字段
    update_data = user_update.model_dump(exclude_unset=True)  # Pydantic v2+
    # update_data = user_update.dict(exclude_unset=True) # Pydantic v1

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update.",
        )

    # 構建更新語句
    update_stmt = (
        update(users_table)
        .where(users_table.c.id == user_id)
        .values(**update_data)
        .returning(users_table)
    )  # 返回更新後的行數據

    try:
        # 執行更新語句
        result = await conn.execute(update_stmt)
        updated_user = result.fetchone()

        if updated_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return UserResponse.model_validate(updated_user)  # Pydantic v2+
        # return UserResponse.from_orm(updated_user) # Pydantic v1

    except Exception as e:
        if "duplicate key value violates unique constraint" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email '{user_update.email}' already exists.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}",
        )


# 刪除用戶
@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int, conn: AsyncConnection = Depends(get_async_connection)
):
    # 構建刪除語句
    delete_stmt = delete(users_table).where(users_table.c.id == user_id)
    # 執行刪除語句
    result = await conn.execute(delete_stmt)

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return  # 204 No Content 響應不需要返回體


@app.post("/auth/login-anonymous")
async def login_anonymous():
    user_id = str(uuid.uuid4())
    token = create_token(user_id)
    return {"access_token": token}


@app.post("/get-user-id")
async def get_user_id(current_user: str = Depends(get_current_user)):
    return {"user_id": current_user}
