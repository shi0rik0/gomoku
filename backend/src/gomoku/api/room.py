from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from gomoku.jwt import get_current_user
from gomoku.state.room_id_manager import room_id_manager
from gomoku.state.server_state import server_state

router = APIRouter(
    prefix="/room", tags=["room"], dependencies=[Depends(get_current_user)]
)


@router.post("/create-room")
async def create_room(current_user: str = Depends(get_current_user)):
    room_id = server_state.create_room(current_user)
    if room_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create room"
        )
    return {"room_id": room_id}


class JoinRoomRequest(BaseModel):
    room_id: str


class SetReadyRequest(BaseModel):
    is_ready: bool


@router.post("/join-room")
async def join_room(data: JoinRoomRequest, player_id: str = Depends(get_current_user)):
    success = server_state.join_room(player_id, data.room_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to join room"
        )
    return {"message": "Joined room successfully"}


@router.post("/leave-room")
async def leave_room(player_id: str = Depends(get_current_user)):
    success = server_state.leave_room(player_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to leave room"
        )
    return {"message": "Left room successfully"}


@router.post("/set-ready")
async def set_ready(
    data: SetReadyRequest, current_user: str = Depends(get_current_user)
):
    success = server_state.set_ready(current_user, data.is_ready)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to set ready status"
        )
    return {"message": "Player ready status updated"}
