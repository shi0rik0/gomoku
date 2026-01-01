"""定义游戏服务器的状态"""

import asyncio
import logging
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Generic, Literal, TypeVar

logger = logging.getLogger(__name__)


@dataclass
class PlayerState:
    """玩家的状态"""

    id: str
    status: Literal["in_room", "in_game"]


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


class SubscribableState(Generic[S, E]):
    """通用的游戏状态"""

    def __init__(self, data: S):
        self.data = data
        self.queues: dict[str, asyncio.Queue[E]] = {}

    def subscribe(self, queue_id: str) -> tuple[asyncio.Queue[E], S]:
        """为玩家订阅消息队列

        注意：返回的 self.data 不能直接修改，否则会影响到状态管理器中的数据"""
        if queue_id not in self.queues:
            self.queues[queue_id] = asyncio.Queue()
        return self.queues[queue_id], self.data

    def unsubscribe(self, queue_id: str):
        """取消玩家的消息队列订阅"""
        if queue_id in self.queues:
            del self.queues[queue_id]
        else:
            logger.warning(f"Queue ID {queue_id} not found during unsubscribe.")

    def update(self, reducer: Callable[[S], tuple[S, E]]):
        """使用 reducer 函数更新状态并通知所有订阅者"""
        self.data, msg = reducer(self.data)
        for qid, queue in self.queues.items():
            try:
                queue.put_nowait(msg)
            except asyncio.QueueFull:
                logger.warning(f"Queue {qid} is full. Skipping message.")


@dataclass
class GameState:
    """游戏的状态"""

    id: str
    board: list[list[int]]
    black_player_id: str
    white_player_id: str
    current_turn: Literal["black", "white"]


@dataclass
class GameStateChange:
    """游戏状态变更消息"""

    game_id: str
    board: list[list[int]]
    current_turn: Literal["black", "white"]


SubscribableRoomState = SubscribableState[RoomState, RoomState]
SubscribableGameState = SubscribableState[GameState, GameStateChange]


class ServerState:
    def __init__(self):
        self.player_state: dict[str, PlayerState] = {}
        self.room_state: dict[str, SubscribableRoomState] = {}
        self.game_state: dict[str, SubscribableGameState] = {}

    def player_create_room(self, player_id: str, room_id: str):
        """玩家创建房间"""
        room = RoomState(
            id=room_id,
            players=[player_id, None],
            host=player_id,
            ready=[False, False],
        )
        self.room_state[room_id] = SubscribableRoomState(room)
        self.player_state[player_id].status = "in_room"

    def player_join_room(self, player_id: str, room_id: str):
        """玩家加入房间"""
        room_state = self.room_state[room_id].data
        for i in range(len(room_state.players)):
            if room_state.players[i] is None:
                room_state.players[i] = player_id
                room_state.ready[i] = False
                break
        self.player_state[player_id].status = "in_room"

    def player_leave_room(self, player_id: str, room_id: str):
        """玩家离开房间"""
        room_state = self.room_state[room_id].data
        for i in range(len(room_state.players)):
            if room_state.players[i] == player_id:
                room_state.players[i] = None
                room_state.ready[i] = False
                break
        del self.player_state[player_id]

    def player_set_ready(self, player_id: str, room_id: str, ready: bool):
        """玩家设置准备状态"""
        room_state = self.room_state[room_id].data
        for i in range(len(room_state.players)):
            if room_state.players[i] == player_id:
                room_state.ready[i] = ready
                break

    def player_start_game(self, room_id: str, game_id: str):
        """玩家开始游戏"""
        room_state = self.room_state[room_id].data
        black_player_id = room_state.players[0]
        white_player_id = room_state.players[1]
        game = GameState(
            id=game_id,
            board=[[0 for _ in range(15)] for _ in range(15)],
            black_player_id=black_player_id,
            white_player_id=white_player_id,
            current_turn="black",
        )
        self.game_state[game_id] = SubscribableGameState(game)
        for player_id in room_state.players:
            if player_id:
                self.player_state[player_id].status = "in_game"
        del self.room_state[room_id]

    def player_delete_room(self, player_id: str, room_id: str):
        """玩家删除房间"""
        room_state = self.room_state[room_id].data
        if room_state.host == player_id:
            for pid in room_state.players:
                if pid and pid in self.player_state:
                    del self.player_state[pid]
            del self.room_state[room_id]

    def game_make_move(self, game_id: str, x: int, y: int) -> bool:
        """玩家在游戏中落子"""
        game_state = self.game_state[game_id].data
        if game_state.board[y][x] != 0:
            return False  # 位置已被占用
        if game_state.current_turn == "black":
            game_state.board[y][x] = 1
            game_state.current_turn = "white"
        else:
            game_state.board[y][x] = 2
            game_state.current_turn = "black"
        return True


# 全局单例
server_state = ServerState()

game_state_example = {
    "player_state": [
        {
            "id": "player1",
            "status": "in_room",
            "room_id": "room1",
        },
        {
            "id": "player2",
            "status": "in_game",
            "game_id": "game1",
        },
    ],
    "room_state": [
        {
            "id": "room1",
            "players": ["player1", "player2"],
            "host": "player1",
            "ready": [True, False],
            "create_time": 1625247600,
        },
        {
            "id": "room2",
            "players": ["player3", None],
            "host": "player3",
            "ready": [False, False],
            "create_time": 1625247700,
        },
    ],
    "game_state": [
        {
            "id": "game1",
            "board": [[0 for _ in range(15)] for _ in range(15)],
            "black_player_id": "player2",
            "white_player_id": "player4",
            "stage": "black_turn",
            "create_time": 1625247800,
        }
    ],
}
