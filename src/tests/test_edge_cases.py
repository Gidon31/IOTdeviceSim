from starlette.testclient import TestClient


async def test_send_command_with_empty_payload(app_client, redis_client):
        device_id = "1"
        await redis_client.hset(f"device:{device_id}", mapping={"status": "normal"})

        r = app_client.post(f"/devices/{device_id}/command", json={})
        assert r.status_code == 400

async def test_get_device_with_very_long_id_returns_404(app_client):
    long_id = "a" * 256
    r = app_client.get(f"/devices/{long_id}")
    assert r.status_code == 404


async def test_send_command_with_boolean_edge_case(app_client, redis_client):
        device_id = "1"
        await redis_client.hset(f"device:{device_id}", mapping={"status": "normal"})

        r = app_client.post(f"/devices/{device_id}/command", json={"online": False})
        assert r.status_code == 200

        saved = await redis_client.hgetall(f"device:{device_id}")

        assert saved["online"] == "false"

async def test_get_devices_handles_corrupted_data(app_client: TestClient, redis_client):

    corrupt_key = "device:corrupt-001"
    valid_key = "device:valid-002"

    await redis_client.hset(corrupt_key, mapping={
        "full_name": "Corrupt Sensor",
        "my_status": "bad",
        "is_online": "true"
    })

    await redis_client.hset(valid_key, mapping={
        "name": "Valid Sensor",
        "type": "thermometer",
        "status": "ready",
        "online": "true"
    })

    response = app_client.get("/devices")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]['id'] == 'valid-002'

def test_get_device_with_special_chars(app_client):
        r = app_client.get("/devices/../..")
        assert r.status_code in (404, 422)
