import json
import redis.asyncio as redis

from src.utils import device_updates_channel
from src.config import logger, DEVICE_COMMAND_CHANNEL


async def write_history_entry(
    r: redis.Redis,
    history_key: str,
    timestamp: str,
    command: dict,
) -> int:
    history_entry = {
        "timestamp": timestamp,
        "command": command,
    }
    return await r.rpush(history_key, json.dumps(history_entry))


async def publish_device_events(
    r: redis.Redis,
    device_id: str,
    updated_fields: dict,
    history_length: int,
    timestamp: str,
) -> None:
    event = {
        "type": "device_command_applied",
        "device_id": device_id,
        "updated_fields": updated_fields,
        "history_length": history_length,
        "timestamp": timestamp,
    }
    message = json.dumps(event)

    await r.publish(device_updates_channel(device_id), message)

    subscribers_count = await r.publish(DEVICE_COMMAND_CHANNEL, message)
    logger.info(f"Published command for {device_id}. Subscribers: {subscribers_count}")
