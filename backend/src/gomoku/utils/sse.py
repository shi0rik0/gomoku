import json
from typing import Any, AsyncGenerator


def to_camel_case(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


def convert_keys_to_camel_case(obj):
    if isinstance(obj, dict):
        return {to_camel_case(k): convert_keys_to_camel_case(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_keys_to_camel_case(item) for item in obj]
    else:
        return obj


async def sse_event_generator(
    generator: AsyncGenerator[Any, None],
) -> AsyncGenerator[str, None]:
    async for event in generator:
        camel_event = convert_keys_to_camel_case(event)
        json_str = json.dumps(camel_event, ensure_ascii=False, separators=(",", ":"))
        yield f"data: {json_str}\n\n"
