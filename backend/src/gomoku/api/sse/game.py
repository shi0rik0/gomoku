import asyncio
from dataclasses import asdict

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from gomoku.jwt import get_current_user_from_query
from gomoku.state.server_state import server_state
from gomoku.utils.sse import sse_event_generator

METHOD = "GET"

NO_RESPONSE_MODEL = True


async def event_generator(game_id: str, player_id: str):
    queue, current_state = server_state.subscribe_game(game_id, player_id)
    try:
        # Yield initial state
        yield {"type": "initial", "state": asdict(current_state)}
        while True:
            change = await queue.get()
            yield {"type": "update", "change": asdict(change)}
    finally:
        server_state.unsubscribe_game(game_id, player_id)


async def handle(game_id: str, player_id: str = Depends(get_current_user_from_query)):
    return StreamingResponse(
        sse_event_generator(event_generator(game_id, player_id)),
        media_type="text/event-stream",
    )
