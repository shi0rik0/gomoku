from fastapi import Depends

from gomoku.jwt import get_current_user
from gomoku.state.server_state import server_state
from gomoku.utils.auto_alias_model import RequestModel, ResponseModel


class Response(ResponseModel):
    success: bool
    room_id: str


async def handle(current_user=Depends(get_current_user)) -> Response:
    room_id = server_state.create_room(current_user)
    if room_id is None:
        return Response(success=False, room_id="")
    return Response(success=True, room_id=room_id)
