"""定义游戏服务器的状态"""

import asyncio
import logging
import uuid
from collections import deque
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


@dataclass
class PlayerStateMatchmaking:

    id: str
    status: Literal["in_matchmaking"] = "in_matchmaking"


PlayerState = PlayerStateInRoom | PlayerStateInGame | PlayerStateMatchmaking


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


@dataclass
class RoomStateChangeGameStart:
    game_id: str
    type: Literal["game_start"] = "game_start"


RoomStateChange = (
    RoomStateChangeUpdate | RoomStateChangeDelete | RoomStateChangeGameStart
)


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
        self._player_state: dict[str, PlayerState] = {}
        self._room_state: dict[str, SubscribableRoomState] = {}
        self._game_state: dict[str, SubscribableGameState] = {}
        self._matchmaking_queue: deque[str] = deque()
        self._matchmaking_task = asyncio.create_task(self._matchmakeing_loop())

    def join_matchmaking(self, player_id: str) -> bool:
        """玩家加入匹配队列"""
        if player_id in self._player_state:
            return False  # 玩家已在房间或游戏中
        if player_id in self._matchmaking_queue:
            return False  # 玩家已在匹配队列中
        self._matchmaking_queue.append(player_id)
        self._player_state[player_id] = PlayerStateMatchmaking(id=player_id)
        return True

    def leave_matchmaking(self, player_id: str) -> bool:
        """玩家离开匹配队列"""
        if player_id not in self._matchmaking_queue:
            return False  # 玩家不在匹配队列中
        self._matchmaking_queue.remove(player_id)
        del self._player_state[player_id]
        return True

    async def _matchmakeing_loop(self):
        """匹配循环，每隔一段时间检查匹配队列，进行匹配"""
        while True:
            await asyncio.sleep(1)  # 每秒检查一次
            while len(self._matchmaking_queue) >= 2:
                player1 = self._matchmaking_queue.popleft()
                player2 = self._matchmaking_queue.popleft()
                room_id = room_id_manager.acquire_room_id()
                room = RoomState(
                    id=room_id,
                    players=[player1, player2],
                    host=player1,
                    ready={player1: True, player2: True},
                )
                self._room_state[room_id] = SubscribableRoomState(room)
                self._player_state[player1] = PlayerStateInRoom(
                    id=player1, room_id=room_id
                )
                self._player_state[player2] = PlayerStateInRoom(
                    id=player2, room_id=room_id
                )
                logger.info(
                    f"Matched players {player1} and {player2} into room {room_id}"
                )

    def subscribe_room(
        self, room_id: str, queue_id: str
    ) -> tuple[asyncio.Queue[RoomStateChange], RoomState]:
        """订阅房间状态更新"""
        return self._room_state[room_id].subscribe(queue_id)

    def unsubscribe_room(self, room_id: str, queue_id: str):
        """取消订阅房间状态更新"""
        self._room_state[room_id].unsubscribe(queue_id)

    def subscribe_game(
        self, game_id: str, queue_id: str
    ) -> tuple[asyncio.Queue[GameStateChange], GameState]:
        """订阅游戏状态更新"""
        return self._game_state[game_id].subscribe(queue_id)

    def unsubscribe_game(self, game_id: str, queue_id: str):
        """取消订阅游戏状态更新"""
        self._game_state[game_id].unsubscribe(queue_id)

    def create_room(self, player_id: str) -> str | None:
        """玩家创建房间，然后以房主身份加入房间"""
        if player_id in self._player_state:
            return None  # 玩家已在房间或游戏中

        room_id = room_id_manager.acquire_room_id()
        if room_id in self._room_state:
            # 理论上不应该发生，但以防万一
            return None

        room = RoomState(
            id=room_id,
            players=[player_id, None],
            host=player_id,
            ready={},
        )
        self._room_state[room_id] = SubscribableRoomState(room)
        self._player_state[player_id] = PlayerStateInRoom(id=player_id, room_id=room_id)
        return room_id

    def join_room(self, player_id: str, room_id: str) -> bool:
        """玩家加入房间"""
        if player_id in self._player_state:
            return False  # 玩家已在房间或游戏中
        room_state = self._room_state[room_id].data
        for i in range(len(room_state.players)):
            if room_state.players[i] is None:
                room_state.players[i] = player_id
                room_state.ready[player_id] = False
                self._player_state[player_id] = PlayerStateInRoom(
                    id=player_id, room_id=room_id
                )
                self._room_state[room_id].notify(
                    RoomStateChangeUpdate(new_state=room_state)
                )
                return True
        return False  # 房间已满

    def leave_room(self, player_id: str) -> bool:
        """玩家离开房间，如果离开的是房主，则删除房间"""
        state = self._player_state.get(player_id)
        if state is None or state.status != "in_room":
            return False

        room_id = state.room_id
        room_state = self._room_state[room_id].data
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
                del self._room_state[room_id]
                del self._player_state[player_id]
                self._room_state[room_id].notify(RoomStateChangeDelete())
                return True
        # 删除玩家状态
        del self._player_state[player_id]
        # 通知房间更新
        if room_id in self._room_state:
            self._room_state[room_id].notify(
                RoomStateChangeUpdate(new_state=room_state)
            )
        return True

    def set_ready(self, player_id: str, ready: bool) -> bool:
        """玩家设置准备状态"""
        state = self._player_state.get(player_id)
        if state is None or state.status != "in_room":
            return False
        room_id = state.room_id
        room_state = self._room_state[room_id].data
        room_state.ready[player_id] = ready
        self._room_state[room_id].notify(RoomStateChangeUpdate(new_state=room_state))
        return True

    def kick_player(self, player_id: str, kicked_player_id: str) -> bool:
        """房主踢出房间内的玩家"""
        state = self._player_state.get(player_id)
        if state is None or state.status != "in_room":
            return False
        room_id = state.room_id
        room_state = self._room_state[room_id].data
        # 检查是否是房主
        if room_state.host != player_id:
            return False
        # 查找并移除被踢玩家
        for i in range(len(room_state.players)):
            if room_state.players[i] == kicked_player_id:
                room_state.players[i] = None
                if kicked_player_id in room_state.ready:
                    del room_state.ready[kicked_player_id]
                del self._player_state[kicked_player_id]
                self._room_state[room_id].notify(
                    RoomStateChangeUpdate(new_state=room_state)
                )
                return True
        return False  # 未找到被踢玩家

    def start_game(self, player_id: str) -> str | None:
        """玩家开始游戏，必须要求房间内所有玩家都已准备"""
        state = self._player_state.get(player_id)
        if state is None or state.status != "in_room":
            logger.info(f"Player {player_id} is not in a room")
            return None
        room_id = state.room_id
        if room_id not in self._room_state:
            logger.info(f"Room {room_id} does not exist")
            return None
        room_state = self._room_state[room_id].data
        # 检查玩家是否是房主
        if room_state.host != player_id:
            logger.info(f"Player {player_id} is not the host of room {room_id}")
            return None
        # 检查房间有两人，且都不是 None
        if (
            len(room_state.players) != 2
            or room_state.players[0] is None
            or room_state.players[1] is None
        ):
            logger.info(f"Room {room_id} does not have two players")
            return None
        # 检查所有玩家都准备好
        for player in room_state.players:
            if player is not None and (
                player != room_state.host and not room_state.ready.get(player, False)
            ):
                logger.info(f"Player {player} is not ready in room {room_id}")
                return None
        # 创建游戏状态
        board: list[list[Literal["black", "white", "empty"]]] = [
            ["empty" for _ in range(15)] for _ in range(15)
        ]
        black_player = room_state.players[0]
        white_player = room_state.players[1]

        game_id = str(uuid.uuid4())
        game = GameState(
            id=game_id,
            board=board,
            black_player_id=black_player,
            white_player_id=white_player,
            current_turn="black",
        )
        self._game_state[game_id] = SubscribableGameState(game)
        # 更新玩家状态
        for player in room_state.players:
            if player is not None:
                self._player_state[player] = PlayerStateInGame(
                    id=player, game_id=game_id
                )
        # 删除房间状态
        self._room_state[room_id].notify(RoomStateChangeGameStart(game_id=game_id))
        del self._room_state[room_id]
        return game_id

    def make_move(self, player_id: str, x: int, y: int) -> bool:
        """玩家在游戏中落子"""
        state = self._player_state.get(player_id)
        if state is None or state.status != "in_game":
            return False

        game_id = state.game_id
        game_state = self._game_state[game_id].data

        # 检查是否轮到该玩家落子
        if (
            game_state.current_turn == "black"
            and game_state.black_player_id != player_id
        ) or (
            game_state.current_turn == "white"
            and game_state.white_player_id != player_id
        ):
            return False
        # 检查落子位置是否合法
        if game_state.board[y][x] != "empty":
            return False
        # 落子
        game_state.board[y][x] = game_state.current_turn
        # 切换回合
        game_state.current_turn = (
            "white" if game_state.current_turn == "black" else "black"
        )
        # 通知订阅者
        self._game_state[game_id].notify(
            GameStateChange(
                who="black" if game_state.current_turn == "white" else "white",
                x=x,
                y=y,
            )
        )
        return True

    def __del__(self):
        self._matchmaking_task.cancel()


# 全局单例
server_state = ServerState()
