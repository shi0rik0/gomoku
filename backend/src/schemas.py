# schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# 用於創建用戶的請求體
class UserCreate(BaseModel):
    name: str
    email: str
    is_active: Optional[bool] = True


# 用於更新用戶的請求體
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None


# 用於響應的用戶數據模型
class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        # 允許從 SQLAlchemy Row 對象的屬性訪問數據
        # 例如 row.id, row.name 而不是 row['id']
        from_attributes = True  # Pydantic v2+
        # orm_mode = True # Pydantic v1
