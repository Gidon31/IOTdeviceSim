import json
from datetime import datetime
from typing import Dict, Any
from src.config import logger
from src.models import Device
from src.utils import prepare_for_redis


async def process_command_message(r, payload: Dict[str, str]):
    device_id = payload.get("device_id")
    command_data = payload.get("command")

    if not device_id or not isinstance(command_data, dict):
        logger.error(f"Invalid command payload: {payload}")
        return

    full_device_id = f"device:{device_id}"
    history_key = f"device:history:{device_id}"

    if not await r.exists(full_device_id):
        logger.warning(f"Device not found: {device_id}")
        return

    valid_keys = set(Device.model_fields.keys())
    command_data = {k: v for k, v in command_data.items() if k in valid_keys}

    if not command_data:
        logger.info(f"No valid fields to update for device {device_id}")
        return

    command = prepare_for_redis(command_data)

    current = await r.hgetall(full_device_id)
    if all(current.get(k) == v for k, v in command.items()):
        logger.info(f"Idempotent command for device {device_id}, skipping")
        return

    await r.hset(full_device_id, mapping=command)

    history_entry = {
        "timestamp": datetime.now().isoformat(),
        "command": command,
    }
    await r.rpush(history_key, json.dumps(history_entry))

    logger.info(f"Updated fields {command} for device {device_id}")
