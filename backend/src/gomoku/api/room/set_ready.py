from fastapi import Depends

from gomoku.jwt import get_current_user
from gomoku.state.server_state import server_state
from gomoku.utils.auto_alias_model import RequestModel, ResponseModel


class Request(RequestModel):
    is_ready: bool


class Response(ResponseModel):
    success: bool


async def handle(request: Request, current_user=Depends(get_current_user)) -> Response:
    success = server_state.set_ready(current_user, request.is_ready)
    return Response(success=success)
