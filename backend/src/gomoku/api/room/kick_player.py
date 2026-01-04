from fastapi import Depends

from gomoku.jwt import get_current_user
from gomoku.state.server_state import server_state
from gomoku.utils.auto_alias_model import RequestModel, ResponseModel


class Response(ResponseModel):
    success: bool


async def handle(
    kicked_player_id: str, player_id: str = Depends(get_current_user)
) -> Response:
    success = server_state.kick_player(player_id, kicked_player_id)
    return Response(success=success)
