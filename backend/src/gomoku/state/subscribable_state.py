import asyncio
import logging
from typing import Any, Callable, Generic, TypeVar

logger = logging.getLogger(__name__)

S = TypeVar("S")  # State 类型
E = TypeVar("E")  # Event/Message 类型


class SubscribableState(Generic[S, E]):
    """通用的游戏状态"""

    def __init__(self, data: S):
        self.data = data
        self._queues: dict[str, asyncio.Queue[E]] = {}

    def subscribe(self, queue_id: str) -> tuple[asyncio.Queue[E], S]:
        """为玩家订阅消息队列

        注意：返回的 self.data 不能直接修改，否则会影响到状态管理器中的数据"""
        if queue_id not in self._queues:
            self._queues[queue_id] = asyncio.Queue()
        return self._queues[queue_id], self.data

    def unsubscribe(self, queue_id: str):
        """取消玩家的消息队列订阅"""
        if queue_id in self._queues:
            del self._queues[queue_id]
        else:
            logger.warning(f"Queue ID {queue_id} not found during unsubscribe.")

    def notify(self, event: E):
        """向所有订阅的玩家发送消息"""
        for queue in self._queues.values():
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning("A player's queue is full; dropping event.")
