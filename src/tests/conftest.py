import json
import os
import random
import pytest
import redis.asyncio as aioredis

from starlette.testclient import TestClient
from src.app import app
from src.config import DB_HOST, DB_PORT, REDIS_DB


@pytest.fixture(scope="function")
async def redis_client():
    client = aioredis.Redis(
        host=DB_HOST,
        port=DB_PORT,
        db=REDIS_DB,
        decode_responses=True
    )
    await client.ping()
    try:
        yield client
    finally:
        await client.aclose()


@pytest.fixture(scope="function", autouse=True)
async def flush_test_db(redis_client):
    db = redis_client.connection_pool.connection_kwargs.get("db")
    assert db == REDIS_DB, (
        f"Refusing to FLUSHDB on db={db}. Expected test db={REDIS_DB}"
    )
    await redis_client.flushdb()
    yield
    await redis_client.flushdb()


@pytest.fixture(scope="session")
def devices_data_realistic():
    file_path = os.getenv("DEVICES_JSON_PATH")
    if not file_path:
        pytest.skip("Skipping: DEVICES_JSON_PATH is not set")
    if not os.path.exists(file_path):
        pytest.skip(f"Skipping: devices json not found at {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise TypeError("JSON file must contain a list of devices.")
    return data


@pytest.fixture(scope="function")
async def populated_devices(redis_client, devices_data_realistic):
    for device_data in devices_data_realistic:
        device_id = device_data["id"]
        full_key = f"device:{device_id}"

        data_to_save = {
            k: str(v).lower() if isinstance(v, bool) else str(v)
            for k, v in device_data.items()
            if k != "id"
        }
        await redis_client.hset(full_key, mapping=data_to_save)

    return devices_data_realistic


@pytest.fixture(params=["missing_device", "existing_device"], scope="function")
async def device_scenario(request, redis_client, devices_data_realistic):
    device = random.choice(devices_data_realistic)
    device_id = device["id"]
    key = f"device:{device_id}"
    history_key = f"device:history:{device_id}"

    await redis_client.delete(key)
    await redis_client.delete(history_key)

    if request.param == "existing_device":
        mapping = {
            k: str(v).lower() if isinstance(v, bool) else str(v)
            for k, v in device.items()
            if k != "id"
        }
        await redis_client.hset(key, mapping=mapping)

    return {"scenario": request.param, "device_id": device_id, "device": device}


@pytest.fixture(params=[
    pytest.param(("valid_update", {"status": "testing_update", "online": False}), id="valid_update"),
    pytest.param(("invalid_keys", {"status": "testing_update", "hacker": "x", "online": True}), id="invalid_keys"),
    pytest.param(("empty", {}), id="empty"),
], scope="function")
def command_payload(request):
    name, payload = request.param
    return {"name": name, "payload": payload}


@pytest.fixture(scope="function")
def app_client():
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
def openapi_schema(app_client: TestClient):
    resp = app_client.get("/openapi.json")
    assert resp.status_code == 200, f"Could not retrieve OpenAPI schema: {resp.status_code}"
    return resp.json()
