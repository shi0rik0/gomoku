from fastapi import Depends

from gomoku.jwt import get_current_user
from gomoku.state.server_state import server_state
from gomoku.utils.auto_alias_model import RequestModel, ResponseModel


class Response(ResponseModel):
    success: bool


async def handle(current_user=Depends(get_current_user)) -> Response:
    success = server_state.leave_room(current_user)
    return Response(success=success)
