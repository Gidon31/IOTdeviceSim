import pytest
from starlette.testclient import TestClient
from src.utils import device_updates_channel
import json


async def test_post_command_success_and_full_update(
        app_client: TestClient,
        redis_client,
        populated_devices
):
    target_id = populated_devices[1]['id']
    new_status = "testing_update"
    new_online = False

    command_payload = {"status": new_status, "online": new_online}

    response = app_client.post(f"/devices/{target_id}/command", json=command_payload)

    assert response.status_code == 200
    assert response.json()['status'] == "success"

    device_state = await redis_client.hgetall(f"device:{target_id}")
    assert device_state['status'] == new_status
    assert device_state['online'] == 'false'

    history = await redis_client.lrange(f"device:history:{target_id}", 0, -1)
    assert len(history) == 1

    history_entry = json.loads(history[0])
    assert history_entry['command']['status'] == new_status

def test_post_command_device_not_found(app_client: TestClient):
    non_existent_id = "device-not-a-chance-command"
    command_payload = {"status": "off"}

    response = app_client.post(f"/devices/{non_existent_id}/command", json=command_payload)

    assert response.status_code == 404
    assert response.json()['detail'] == f"Device not found: {non_existent_id}"

async def test_send_command_ignores_unknown_fields_and_updates_only_valid(app_client, redis_client):
    device_id = "1"
    await redis_client.hset(f"device:{device_id}", mapping={"status": "normal", "online": "true"})

    payload = {"status": "normal", "hacker_field": "kuku"}

    r = app_client.post(f"/devices/{device_id}/command", json=payload)
    assert r.status_code == 200
    saved = await redis_client.hgetall(f"device:{device_id}")
    assert "status" in saved
    assert "hacker_field" not in saved


async def test_command_publishes_event(redis_client, app_client):
    device_id = "1"
    await redis_client.hset(f"device:{device_id}", mapping={"status": "normal"})

    channel = device_updates_channel(device_id)

    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel)

    await pubsub.get_message(timeout=1)

    app_client.post(f"/devices/{device_id}/command", json={"status": "error"})

    message = None
    for _ in range(20):
        message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.1)
        if message:
            break

    assert message is not None

async def test_command_creates_history_entry(app_client, redis_client):
    await redis_client.hset("device:1", mapping={"status": "normal"})

    app_client.post("/devices/1/command", json={"status": "warning"})

    history = await redis_client.lrange("device:history:1", 0, -1)
    assert len(history) == 1
