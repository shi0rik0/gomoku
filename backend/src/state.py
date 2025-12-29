"""定义游戏服务器的状态"""

import asyncio
from dataclasses import dataclass
from enum import Enum


class PlayerStatus(str, Enum):
    IN_ROOM = "in_room"
    IN_GAME = "in_game"


@dataclass
class PlayerState:
    """玩家的状态"""

    id: str
    name: str
    status: PlayerStatus
    lock: asyncio.Lock = asyncio.Lock()


@dataclass
class RoomState:
    """游戏房间的状态"""

    id: str
    players: list[str]
    host: str
    ready: list[bool]


@dataclass
class ServerState:
    """服务器的整体状态"""

    rooms: dict[str, RoomState]
    players: dict[str, PlayerState]


server_state = ServerState(rooms={}, players={})
