from typing import List
from fastapi import APIRouter, Depends
import redis.asyncio as redis
from src.dependencies import get_redis
from src.models import Device, ReturnObject
from src.services.device_service import list_devices, fetch_device, apply_command

router = APIRouter(
    prefix="/devices",
    tags=["Devices"]
)

@router.get("/status")
async def basic_status_check():
    return {"status": "ok"}


@router.get("/", response_model=List[Device])
async def get_devices(r: redis.Redis = Depends(get_redis)):
    return await list_devices(r)


@router.get("/{device_id}", response_model=Device)
async def get_device(device_id: str, r: redis.Redis = Depends(get_redis)):
    return await fetch_device(r, device_id)


@router.post("/{device_id}/command", response_model=ReturnObject)
async def send_command(device_id: str, command: dict, r: redis.Redis = Depends(get_redis)):
    return await apply_command(r, device_id, command)
from typing import List
