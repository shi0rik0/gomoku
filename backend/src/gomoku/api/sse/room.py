import asyncio
from dataclasses import asdict

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from gomoku.jwt import get_current_user_from_query
from gomoku.state.server_state import server_state
from gomoku.utils.sse import sse_event_generator

METHOD = "GET"

NO_RESPONSE_MODEL = True


async def event_generator(room_id: str, player_id: str):
    queue, current_state = server_state.subscribe_room(room_id, player_id)
    try:
        # Yield initial state
        yield {"type": "initial", "state": asdict(current_state)}
        while True:
            change = await queue.get()
            yield asdict(change)
    finally:
        server_state.unsubscribe_room(room_id, player_id)


async def handle(room_id: str, player_id: str = Depends(get_current_user_from_query)):
    return StreamingResponse(
        sse_event_generator(event_generator(room_id, player_id)),
        media_type="text/event-stream",
    )
