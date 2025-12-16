import json
from datetime import datetime ,timezone
from typing import List
from fastapi import APIRouter, Depends
import redis.asyncio as redis
from src.dependencies import get_redis
from src.models import Device, ReturnObject
from src.utils import prepare_device_data, device_updates_channel, prepare_for_redis
from src.config import logger, DEVICE_COMMAND_CHANNEL

router = APIRouter(
    prefix="/devices",
    tags=["Devices"]
)

@router.get("/status")
async def basic_status_check():
    return {"status": "ok"}

@router.get("/", response_model=List[Device])
async def get_devices(r: redis.Redis = Depends(get_redis)):

    print("GET /devices path reached")


    devices_list = []
    device_keys_async = r.scan_iter(match='device:*')

    async for key in device_keys_async:
        device_data_raw = await r.hgetall(key)

        if device_data_raw:
            try:
                prepared_data = prepare_device_data(key, device_data_raw)
                device = Device.model_validate(prepared_data)
                devices_list.append(device)
                print(f"Fetched and appended device: {device} ")
            except Exception as e:
                logger.error(f"Skipping invalid device key {key}. Validation Error: {e}")



    return devices_list


from fastapi import HTTPException

@router.get("/{device_id}", response_model=Device)
async def get_device(device_id: str, r: redis.Redis = Depends(get_redis)):
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


@router.post("/{device_id}/command", response_model=ReturnObject)
async def send_command(device_id: str, command: dict, r: redis.Redis = Depends(get_redis)):
    logger.debug(f"POST /devices/{device_id}/command path reached with command {command}")

    full_device_id = f"device:{device_id}"
    history_key = f"device:history:{device_id}"

    if not await r.exists(full_device_id):
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")

    VALID_KEYS = set(Device.model_fields.keys())
    invalid_keys = set(command.keys()) - VALID_KEYS

    if invalid_keys:
        print(f"Error: Found unknown fields: {', '.join(invalid_keys)} that will be removed from update")
        for key in invalid_keys:
            command.pop(key, None)

    if not command:
        raise HTTPException(status_code=400, detail="Command payload cannot be empty")

    current = await r.hgetall(full_device_id)
    if all(current.get(k) == str(v) for k, v in command.items()):
        return ReturnObject(
            device_id=device_id,
            status="success",
            message="No changes applied – command is idempotent"
        )

    command = prepare_for_redis(command)
    await r.hset(full_device_id, mapping=command)

    history_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
    }
    list_length = await r.rpush(history_key, json.dumps(history_entry))

    event = {
        "type": "device_command_applied",
        "device_id": device_id,
        "updated_fields": command,
        "history_length": list_length,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    message = json.dumps(event)

    await r.publish(device_updates_channel(device_id), json.dumps(event))

    subscribers_count = await r.publish(DEVICE_COMMAND_CHANNEL, message)
    logger.info(f"Published command for {device_id}. Subscribers: {subscribers_count}")

    message = f"Updated fields: {command} for device: {device_id}"

    return ReturnObject(device_id=device_id,
                        status="success",
                        message=message)
