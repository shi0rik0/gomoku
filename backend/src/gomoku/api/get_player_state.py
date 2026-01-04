from dataclasses import asdict
from typing import Literal

from fastapi import Depends

from gomoku.jwt import get_current_user
from gomoku.state.server_state import server_state
from gomoku.utils.auto_alias_model import RequestModel, ResponseModel


class Response(ResponseModel):
    status: Literal["idle", "in_room", "in_game"]
    room_id: str | None = None
    game_id: str | None = None


async def handle(player_id=Depends(get_current_user)) -> dict:
    player_state = server_state._player_state.get(player_id)
    if player_state is None:
        return {"id": player_id, "status": "idle"}
    return asdict(player_state)
