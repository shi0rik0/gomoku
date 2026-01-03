# database.py
import os
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    async_sessionmaker,
    create_async_engine,
)

from gomoku.env import ENV, SQL_DATABASE, SQL_HOST, SQL_PASSWORD, SQL_PORT, SQL_USER

# 從環境變量獲取數據庫 URL，如果沒有則使用默認值
# 格式: postgresql+asyncpg://user:password@host:port/dbname
DATABASE_URL = f"postgresql+asyncpg://{SQL_USER}:{SQL_PASSWORD}@{SQL_HOST}:{SQL_PORT}/{SQL_DATABASE}"

DEBUG = ENV == "dev"

# 創建異步引擎
# echo=True 會在控制台打印所有執行的 SQL 語句，方便調試
async_engine = create_async_engine(DATABASE_URL, echo=DEBUG)

# 創建一個異步會話工廠 (雖然我們不直接使用ORM的Session，但AsyncConnection可以從這裡獲取)
# expire_on_commit=False 對於 Core-only 使用不是嚴格必要的，但對於 ORM 會話很重要
# async_session = async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession) # 如果要用 AsyncSession


# 數據庫初始化函數，用於在應用啟動時創建表
async def init_db(metadata):
    """
    在應用啟動時，使用異步引擎創建所有定義的表。
    注意：metadata.create_all() 是同步方法，不能直接在異步連接上使用。
    我們需要通過異步連接執行原始 DDL 語句，或者使用 SQLAlchemy 的同步引擎部分。
    對於簡單的初始化，直接執行 DDL 語句更常見。
    """
    async with async_engine.begin() as conn:
        # 這裡我們手動執行 DDL 語句，或者使用 alembic 等遷移工具
        # 為了演示，我們直接執行 CREATE TABLE IF NOT EXISTS
        # 更好的做法是使用 alembic 進行數據庫遷移管理
        await conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL
            );
        """
            )
        )
        print("Database tables ensured.")


# 依賴注入函數，為每個請求提供一個異步數據庫連接
async def get_async_connection() -> AsyncGenerator[AsyncConnection, None]:
    """
    為每個請求提供一個異步數據庫連接。
    連接會在請求結束後自動關閉並返回連接池。
    """
    async with async_engine.begin() as conn:  # 使用 begin() 會自動管理事務
        try:
            yield conn
        finally:
            # conn 會在 with 語句結束時自動關閉並返回連接池
            pass


# 應用關閉時清理引擎
async def shutdown_db():
    """
    在應用關閉時關閉數據庫引擎，釋放所有連接。
    """
    await async_engine.dispose()
    print("Database engine disposed.")
