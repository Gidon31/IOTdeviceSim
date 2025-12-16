import json
import os
import random
import pytest
import redis.asyncio as aioredis
from asgi_lifespan import LifespanManager
from starlette.testclient import TestClient
from src.app import app
from src.config import DB_HOST, DB_PORT



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
async def redis_client():

    print("\n--- Redis: Setting up test client ---")

    client = aioredis.Redis(
        host=DB_HOST,
        port=DB_PORT,
        decode_responses=True
    )

    try:
        await client.ping()
        yield client

    finally:
        print("\n--- Redis: Closing client connection ---")
        await client.close()



REDIS_DB = int(os.getenv("REDIS_DB", "0"))
@pytest.fixture(scope="function", autouse=True)
async def flush_test_db(redis_client):
    db = redis_client.connection_pool.connection_kwargs.get("db")

    assert db == REDIS_DB, f"Refusing to FLUSHDB on db={db}. Expected test db={REDIS_DB}"

    await redis_client.flushdb()
    yield
    await redis_client.flushdb()

@pytest.fixture(scope="session")
def devices_data_realistic():
    file_path = os.getenv("DEVICES_JSON_PATH")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

            if not isinstance(data, list):
                raise TypeError("JSON file must contain a list of devices.")

            return data

    except FileNotFoundError:
        pytest.skip(f"Skipping tests: Test data file not found at {file_path}")

    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding JSON file: {e}")


@pytest.fixture(scope="function")
async def populated_devices(redis_client, devices_data_realistic):

    print("--- Redis: Populating test data from JSON file ---")

    for device_data in devices_data_realistic:
        device_id = device_data["id"]
        full_key = f"device:{device_id}"

        data_to_save = {
            k: str(v).lower() if isinstance(v, bool) else str(v)
            for k, v in device_data.items()
            if k != 'id'
        }

        await redis_client.hset(full_key, mapping=data_to_save)

    return devices_data_realistic



@pytest.fixture(scope="session")
async def app_client():
    async with LifespanManager(app):
        client = TestClient(app)

        print("\n--- App: FastAPI Lifespan Started ---")
        yield client
        print("\n--- App: FastAPI Lifespan Ended ---")


@pytest.fixture(scope="session")
def openapi_schema(app_client: TestClient):
    print("\n--- Swagger: Retrieving OpenAPI Schema ---")

    response = app_client.get("/openapi.json")

    # Ensure the request was successful
    if response.status_code != 200:
        pytest.fail(f"Could not retrieve OpenAPI schema: Status {response.status_code}")

    return response.json()