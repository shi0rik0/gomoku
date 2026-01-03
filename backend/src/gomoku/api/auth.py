import logging
import uuid

from fastapi import APIRouter, Depends

from gomoku.jwt import create_token, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login-anonymous")
async def login_anonymous():
    user_id = str(uuid.uuid4())
    token = create_token(user_id)
    logger.info(f"Anonymous user logged in with ID: {user_id}")
    return {"access_token": token}


@router.post("/verify-token")
async def verify_token_endpoint(current_user: str = Depends(get_current_user)):
    return {"user_id": current_user}
