from fastapi import Depends

from gomoku.jwt import get_current_user
from gomoku.state.server_state import server_state
from gomoku.utils.auto_alias_model import RequestModel, ResponseModel


class Request(RequestModel):
    room_id: str


class Response(ResponseModel):
    success: bool


async def handle(request: Request, current_user=Depends(get_current_user)) -> Response:
    success = server_state.join_room(current_user, request.room_id)
    return Response(success=success)
