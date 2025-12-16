import json
from starlette.testclient import TestClient


def test_app_starts_and_is_healthy(app_client: TestClient):
    response = app_client.get("/devices/status")
    response_json = json.loads(response.text)
    assert response.status_code == 200
    assert response_json["status"] == "ok"