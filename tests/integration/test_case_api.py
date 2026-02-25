from fastapi.testclient import TestClient

from src.api.main import app
from tests.integration.auth_helpers import build_api_key_headers


def test_create_and_list_case() -> None:
    client = TestClient(app)
    headers = build_api_key_headers(client)
    payload = {
        "alert_id": "a-1",
        "account_id": "acct-7",
        "symbol": "AAPL",
        "severity": "high",
        "summary": "Test suspicious pattern",
    }
    create_resp = client.post("/cases", json=payload, headers=headers)
    assert create_resp.status_code == 200

    list_resp = client.get("/cases", headers=headers)
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert len(data) >= 1
