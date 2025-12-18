import pytest
from starlette.testclient import TestClient



def test_loads_devices(devices_data_realistic):
    assert isinstance(devices_data_realistic, list)
    assert len(devices_data_realistic) > 0

async def test_get_devices_empty_list(app_client: TestClient, redis_client):

    response = app_client.get("/devices")
    assert response.status_code == 200
    assert response.json() == []

async def test_get_devices_returns_populated_data(app_client: TestClient, populated_devices):

    response = app_client.get("/devices")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == len(populated_devices)

    def sort_key(device):
        return device['id']

    sorted_populated = sorted(populated_devices, key=sort_key)
    sorted_data = sorted(data, key=sort_key)
    assert sorted_populated == sorted_data


def test_get_device_not_found(app_client: TestClient):

    non_existent_id = "device-not-a-chance"

    response = app_client.get(f"/devices/{non_existent_id}")

    assert response.status_code == 404
    assert response.json()['detail'] == f"Device not found with id: {non_existent_id}"

@pytest.mark.asyncio
async def test_command_is_idempotent(app_client, redis_client):

        await redis_client.hset("device:1", mapping={"status": "normal"})

        app_client.post("/devices/1/command", json={"status": "normal"})
        app_client.post("/devices/1/command", json={"status": "normal"})

        saved = await redis_client.hgetall("device:1")
        assert saved["status"] == "normal"
