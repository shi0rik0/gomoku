import logging
import uuid

from fastapi import APIRouter, Depends

from gomoku.jwt import create_token, get_current_user
from gomoku.utils.auto_alias_model import RequestModel, ResponseModel

logger = logging.getLogger(__name__)


class Response(ResponseModel):
    access_token: str


async def handle() -> Response:
    user_id = str(uuid.uuid4())
    token = create_token(user_id)
    logger.info(f"Anonymous user logged in with ID: {user_id}")
    return Response(access_token=token)
