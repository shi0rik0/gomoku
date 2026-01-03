import asyncio

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from gomoku.jwt import get_current_user_from_query
from gomoku.utils.sse import sse_event_generator

router = APIRouter(
    prefix="/sse/game",
    tags=["sse"],
    dependencies=[Depends(get_current_user_from_query)],
)


async def dummy_event_generator(player_id: str):
    while True:
        await asyncio.sleep(5)
        yield {
            "msg": f"Hello, player {player_id}! The server time is {asyncio.get_event_loop().time()}"
        }


@router.get("/events")
async def get_game_events(player_id: str = Depends(get_current_user_from_query)):
    return StreamingResponse(
        sse_event_generator(dummy_event_generator(player_id)),
        media_type="text/event-stream",
    )
