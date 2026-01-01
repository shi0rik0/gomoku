# models.py
from sqlalchemy import Boolean, Column, DateTime, Integer, MetaData, String, Table
from sqlalchemy.sql import func

from backend.src.gomoku.utils.not_null_column import NotNullColumn

# MetaData 對象是所有表定義的容器
metadata = MetaData()

# 定義 users 表
users_table = Table(
    "users",
    metadata,
    NotNullColumn("id", Integer, primary_key=True, autoincrement=True),
    NotNullColumn("name", String(50), unique=True),
    NotNullColumn("email", String(100), unique=True),
    NotNullColumn("password_hash", String(256)),
    NotNullColumn("created_at", DateTime, server_default=func.now()),
    NotNullColumn("updated_at", DateTime),
)
