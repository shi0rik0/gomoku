"""定义游戏服务器的状态"""

import asyncio
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Generic, Literal, TypeVar


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

    id: str  # 房间 ID
    players: list[str | None]  # 玩家 ID 列表
    host: str  # 房主 ID
    ready: list[bool]  # 每个玩家的准备状态

    def to_json(self):
        return {
            "id": self.id,
            "players": self.players,
            "host": self.host,
            "ready": self.ready,
        }


S = TypeVar("S")  # State 类型
E = TypeVar("E")  # Event/Message 类型


class GeneralStateManager(Generic[S, E]):
    """通用的游戏状态"""

    def __init__(self, data: S):
        self.data = data
        self.queues: dict[str, asyncio.Queue[E]] = {}
        self.lock = asyncio.Lock()

    async def subscribe(self, player_id: str) -> tuple[asyncio.Queue[E], S]:
        """为玩家订阅消息队列"""
        async with self.lock:
            if player_id not in self.queues:
                self.queues[player_id] = asyncio.Queue()
            return self.queues[player_id], deepcopy(self.data)

    async def unsubscribe(self, player_id: str):
        """取消玩家的消息队列订阅"""
        async with self.lock:
            if player_id in self.queues:
                del self.queues[player_id]

    async def update(self, reducer: Callable[[S], tuple[S, E]]):
        """使用 reducer 函数更新状态并通知所有订阅者"""
        async with self.lock:
            data, msg = reducer(deepcopy(self.data))
            self.data = deepcopy(data)
            for queue in self.queues.values():
                await queue.put(deepcopy(msg))


# 因为 RoomState 比较小，所以没必要用事件进行增量更新
# 这里直接用 RoomState 作为事件类型
RoomStateManager = GeneralStateManager[RoomState, RoomState]

room_state_managers_lock = asyncio.Lock()
room_state_managers: dict[str, RoomStateManager] = {}


@dataclass
class GameState:
    """游戏的状态"""

    id: str
    board: list[list[int]]
    black_player_id: str
    white_player_id: str
    current_turn: Literal["black", "white"]


@dataclass
class ServerState:
    """服务器的整体状态"""

    rooms: dict[str, RoomState]
    players: dict[str, PlayerState]
    games: dict[str, GameState]


server_state = ServerState(rooms={}, players={}, games={})
