from fastapi.testclient import TestClient

from src.api.main import app


def test_create_and_list_case() -> None:
    client = TestClient(app)
    payload = {
        "alert_id": "a-1",
        "account_id": "acct-7",
        "symbol": "AAPL",
        "severity": "high",
        "summary": "Test suspicious pattern",
    }
    create_resp = client.post("/cases", json=payload)
    assert create_resp.status_code == 200

    list_resp = client.get("/cases")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert len(data) >= 1
