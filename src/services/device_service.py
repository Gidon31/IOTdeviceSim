import json
from datetime import datetime, timezone
from typing import List, Dict, Any

import redis.asyncio as redis
from fastapi import HTTPException

from src.models import Device, ReturnObject
from src.utils import prepare_device_data, prepare_for_redis
from src.config import logger
from src.services.device_events import write_history_entry, publish_device_events


async def list_devices(r: redis.Redis) -> List[Device]:
    logger.debug("GET /devices path reached")

    devices_list: List[Device] = []
    device_keys_async = r.scan_iter(match="device:*")

    async for key in device_keys_async:
        device_data_raw = await r.hgetall(key)
        if not device_data_raw:
            continue

        try:
            prepared_data = prepare_device_data(key, device_data_raw)
            device = Device.model_validate(prepared_data)
            devices_list.append(device)
        except Exception as e:
            logger.error(f"Skipping invalid device key {key}. Validation Error: {e}")

    return devices_list


async def fetch_device(r: redis.Redis, device_id: str) -> Device:
    logger.debug(f"GET /devices/{device_id} path reached")
    full_device_id = f"device:{device_id}"

    if not await r.exists(full_device_id):
        logger.debug(f"Device not found with ID: {device_id}")
        raise HTTPException(status_code=404, detail=f"Device not found with id: {device_id}")

    device_data_raw = await r.hgetall(full_device_id)
    if not device_data_raw:
        raise HTTPException(status_code=404, detail=f"Device not found with id: {device_id}")

    try:
        prepared_data = prepare_device_data(full_device_id, device_data_raw)
        return Device.model_validate(prepared_data)
    except Exception as e:
        logger.exception(f"failed to fetch device data of device id: {device_id}, error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch device data")


async def apply_command(r: redis.Redis, device_id: str, command: Dict[str, Any]) -> ReturnObject:
    logger.debug(f"POST /devices/{device_id}/command path reached with command {command}")

    full_device_id = f"device:{device_id}"
    history_key = f"device:history:{device_id}"

    if not await r.exists(full_device_id):
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")

    command = _sanitize_command(command)

    if not command:
        raise HTTPException(status_code=400, detail="Command payload cannot be empty")

    current = await r.hgetall(full_device_id)
    if _is_idempotent(current, command):
        return ReturnObject(
            device_id=device_id,
            status="success",
            message="No changes applied – command is idempotent"
        )

    command_for_redis = prepare_for_redis(command)
    await r.hset(full_device_id, mapping=command_for_redis)

    timestamp = datetime.now(timezone.utc).isoformat()
    list_length = await write_history_entry(r, history_key, timestamp, command_for_redis)

    await publish_device_events(
        r=r,
        device_id=device_id,
        updated_fields=command_for_redis,
        history_length=list_length,
        timestamp=timestamp,
    )

    message = f"Updated fields: {command_for_redis} for device: {device_id}"
    return ReturnObject(device_id=device_id, status="success", message=message)


def _sanitize_command(command: Dict[str, Any]) -> Dict[str, Any]:
    VALID_KEYS = set(Device.model_fields.keys())
    invalid_keys = set(command.keys()) - VALID_KEYS

    if invalid_keys:
        logger.warning(
            f"Found unknown fields: {', '.join(invalid_keys)} that will be removed from update"
        )
        for key in invalid_keys:
            command.pop(key, None)

    return command


def _is_idempotent(current: Dict[str, Any], command: Dict[str, Any]) -> bool:
    return all(current.get(k) == str(v) for k, v in command.items())
