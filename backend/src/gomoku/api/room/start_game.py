from fastapi import Depends

from gomoku.jwt import get_current_user
from gomoku.state.server_state import server_state
from gomoku.utils.auto_alias_model import RequestModel, ResponseModel


class Response(ResponseModel):
    success: bool
    game_id: str


async def handle(player_id=Depends(get_current_user)) -> Response:
    game_id = server_state.start_game(player_id)
    success = game_id is not None
    if game_id is None:
        game_id = ""
    return Response(success=success, game_id=game_id)
