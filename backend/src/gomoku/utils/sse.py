import json
from typing import Any, AsyncGenerator


async def sse_event_generator(
    generator: AsyncGenerator[Any, None],
) -> AsyncGenerator[str, None]:
    async for event in generator:
        json_str = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
        yield f"data: {json_str}\n\n"
