import json
import pytest


async def test_send_command_parametrized(app_client, redis_client, device_scenario, command_payload):
    device_id = device_scenario["device_id"]
    scenario = device_scenario["scenario"]
    payload_name = command_payload["name"]
    payload = command_payload["payload"]

    resp = app_client.post(f"/devices/{device_id}/command", json=payload)
    if scenario == "missing_device":
        assert resp.status_code == 404
        return
    if payload_name == "empty":
        assert resp.status_code == 400
        return
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    state = await redis_client.hgetall(f"device:{device_id}")
    if payload_name == "invalid_keys":
        assert "hacker" not in state
    for k, v in payload.items():
        if k in ("hacker",):
            continue
        expected = str(v).lower() if isinstance(v, bool) else str(v)
        assert state.get(k) == expected
    history = await redis_client.lrange(f"device:history:{device_id}", 0, -1)
    assert len(history) == 1
    history_entry = json.loads(history[0])
    assert history_entry["command"]["status"] == str(payload.get("status", state.get("status")))
