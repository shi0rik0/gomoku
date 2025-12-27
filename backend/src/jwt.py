"""JWT认证相关的逻辑"""

from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyQuery

from env import JWT_SECRET, JWT_EXPIRE_MINUTES

SECRET_KEY = JWT_SECRET
ALGORITHM = "HS256"

security = HTTPBearer()  # 用于解析 Authorization: Bearer <token>


# 1. 生成 Token
def create_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": user_id, "exp": expire}  # subject  # expiration
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# 2. 验证 Token
def verify_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")  # 返回 user_id
    except ExpiredSignatureError:
        # print("Token expired")
        return None
    except JWTError:
        # print("Invalid token")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    token = credentials.credentials
    user_id = verify_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


# 创建安全依赖
token_query = APIKeyQuery(name="token", auto_error=True)


async def get_current_player_from_query(token: str = Security(token_query)) -> str:
    """从 query 参数验证 JWT Token"""
    player_id = verify_token(token)
    if player_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )
    return player_id
