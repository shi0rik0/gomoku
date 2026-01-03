"""定义游戏服务器的状态"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Literal

from gomoku.state.room_id_manager import room_id_manager
from gomoku.state.subscribable_state import SubscribableState

logger = logging.getLogger(__name__)


@dataclass
class PlayerStateInRoom:

    id: str
    room_id: str
    status: Literal["in_room"] = "in_room"


@dataclass
class PlayerStateInGame:

    id: str
    game_id: str
    status: Literal["in_game"] = "in_game"


PlayerState = PlayerStateInRoom | PlayerStateInGame


@dataclass
class RoomState:
    """游戏房间的状态"""

    id: str  # 房间 ID
    players: list[str | None]  # 玩家 ID 列表
    host: str  # 房主 ID
    ready: dict[str, bool]  # 玩家准备状态，房主默认已准备


@dataclass
class RoomStateChangeUpdate:
    new_state: RoomState
    type: Literal["update"] = "update"


@dataclass
class RoomStateChangeDelete:
    type: Literal["delete"] = "delete"


RoomStateChange = RoomStateChangeUpdate | RoomStateChangeDelete


@dataclass
class GameState:
    """游戏的状态"""

    id: str
    board: list[list[Literal["black", "white", "empty"]]]
    black_player_id: str
    white_player_id: str
    current_turn: Literal["black", "white"]


@dataclass
class GameStateChange:
    """游戏状态变更消息"""

    who: Literal["black", "white"]
    x: int
    y: int


SubscribableRoomState = SubscribableState[RoomState, RoomStateChange]
SubscribableGameState = SubscribableState[GameState, GameStateChange]


class ServerState:
    def __init__(self):
        self.player_state: dict[str, PlayerState] = {}
        self.room_state: dict[str, SubscribableRoomState] = {}
        self.game_state: dict[str, SubscribableGameState] = {}

    def subscribe_room(
        self, room_id: str, queue_id: str
    ) -> tuple[asyncio.Queue[RoomStateChange], RoomState]:
        """订阅房间状态更新"""
        return self.room_state[room_id].subscribe(queue_id)

    def unsubscribe_room(self, room_id: str, queue_id: str):
        """取消订阅房间状态更新"""
        self.room_state[room_id].unsubscribe(queue_id)

    def create_room(self, player_id: str) -> str | None:
        """玩家创建房间，然后以房主身份加入房间"""
        if player_id in self.player_state:
            return None  # 玩家已在房间或游戏中

        room_id = room_id_manager.acquire_room_id()
        if room_id in self.room_state:
            # 理论上不应该发生，但以防万一
            return None

        room = RoomState(
            id=room_id,
            players=[player_id, None],
            host=player_id,
            ready={},
        )
        self.room_state[room_id] = SubscribableRoomState(room)
        self.player_state[player_id] = PlayerStateInRoom(id=player_id, room_id=room_id)
        return room_id

    def join_room(self, player_id: str, room_id: str) -> bool:
        """玩家加入房间"""
        if player_id in self.player_state:
            return False  # 玩家已在房间或游戏中
        room_state = self.room_state[room_id].data
        for i in range(len(room_state.players)):
            if room_state.players[i] is None:
                room_state.players[i] = player_id
                room_state.ready[player_id] = False
                self.player_state[player_id] = PlayerStateInRoom(
                    id=player_id, room_id=room_id
                )
                self.room_state[room_id].notify(
                    RoomStateChangeUpdate(new_state=room_state)
                )
                return True
        return False  # 房间已满

    def leave_room(self, player_id: str) -> bool:
        """玩家离开房间，如果离开的是房主，则删除房间"""
        state = self.player_state.get(player_id)
        if state is None or state.status != "in_room":
            return False

        room_id = state.room_id
        room_state = self.room_state[room_id].data
        # 从玩家列表中移除
        for i in range(len(room_state.players)):
            if room_state.players[i] == player_id:
                room_state.players[i] = None
                break
        # 从准备状态中删除
        if player_id in room_state.ready:
            del room_state.ready[player_id]
        # 如果是房主，且还有其他玩家，选择新房主
        if room_state.host == player_id:
            remaining_players = [p for p in room_state.players if p is not None]
            if remaining_players:
                room_state.host = remaining_players[0]
            else:
                # 房间空了，删除房间
                del self.room_state[room_id]
                del self.player_state[player_id]
                self.room_state[room_id].notify(RoomStateChangeDelete())
                return True
        # 删除玩家状态
        del self.player_state[player_id]
        # 通知房间更新
        if room_id in self.room_state:
            self.room_state[room_id].notify(RoomStateChangeUpdate(new_state=room_state))
        return True

    def set_ready(self, player_id: str, ready: bool) -> bool:
        """玩家设置准备状态"""
        state = self.player_state.get(player_id)
        if state is None or state.status != "in_room":
            return False
        room_id = state.room_id
        room_state = self.room_state[room_id].data
        room_state.ready[player_id] = ready
        self.room_state[room_id].notify(RoomStateChangeUpdate(new_state=room_state))
        return True

    def start_game(self, room_id: str, game_id: str) -> bool:
        """玩家开始游戏，必须要求房间内所有玩家都已准备"""
        if room_id not in self.room_state:
            return False
        room_state = self.room_state[room_id].data
        # 检查房间有两人，且都不是 None
        if (
            len(room_state.players) != 2
            or room_state.players[0] is None
            or room_state.players[1] is None
        ):
            return False
        # 检查所有玩家都准备好
        for player in room_state.players:
            if player is not None and not room_state.ready.get(player, False):
                return False
        # 创建游戏状态
        board: list[list[Literal["black", "white", "empty"]]] = [
            ["empty" for _ in range(15)] for _ in range(15)
        ]
        black_player = room_state.players[0]
        white_player = room_state.players[1]
        game = GameState(
            id=game_id,
            board=board,
            black_player_id=black_player,
            white_player_id=white_player,
            current_turn="black",
        )
        self.game_state[game_id] = SubscribableGameState(game)
        # 更新玩家状态
        for player in room_state.players:
            if player is not None:
                self.player_state[player] = PlayerStateInGame(
                    id=player, game_id=game_id
                )
        # 删除房间状态
        del self.room_state[room_id]
        return True


# 全局单例
server_state = ServerState()
