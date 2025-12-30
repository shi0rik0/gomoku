import asyncio
import logging
import random
from collections import deque

logger = logging.getLogger(__name__)

LEASE_DURATION = 1000 * 60  # 房间ID租赁时长，单位秒


class RoomIDManager:
    def __init__(self):
        self.lock = asyncio.Lock()
        ids = [f"{i:06d}" for i in range(1000000)]
        random.shuffle(ids)
        self.queue = deque(ids)

        self.allocated_ids = {}
        self._cleanup_expired_ids_task = asyncio.create_task(
            self._cleanup_expired_ids()
        )

    async def acquire_room_id(self) -> str:
        async with self.lock:
            if not self.queue:
                raise RuntimeError("No available room IDs")
            return self.queue.popleft()

    async def release_room_id(self, room_id: str):
        async with self.lock:
            self.queue.append(room_id)

    async def renew_lease(self, room_id: str):
        async with self.lock:
            if room_id in self.allocated_ids:
                self.allocated_ids[room_id] = asyncio.get_event_loop().time()
            else:
                logger.warning(
                    f"Attempted to renew lease for unallocated room ID: {room_id}"
                )

    async def _cleanup_expired_ids(self):
        while True:
            await asyncio.sleep(60)  # 每分钟检查一次
            current_time = asyncio.get_event_loop().time()
            async with self.lock:
                expired_ids = [
                    room_id
                    for room_id, lease_time in self.allocated_ids.items()
                    if current_time - lease_time > LEASE_DURATION
                ]
                for room_id in expired_ids:
                    del self.allocated_ids[room_id]
                    self.queue.append(room_id)

    def __del__(self):
        self._cleanup_expired_ids_task.cancel()


# 全局单例
room_id_manager = RoomIDManager()
