from datetime import datetime, timezone

from fastapi.testclient import TestClient

from src.api.main import app
from tests.integration.auth_helpers import build_api_key_headers


def test_ingest_endpoint_accepts_event() -> None:
    client = TestClient(app)
    headers = build_api_key_headers(client)
    payload = {
        "event_id": "evt-1",
        "ts": datetime.now(timezone.utc).isoformat(),
        "venue": "NASDAQ",
        "asset_class": "equity",
        "symbol": "AAPL.US",
        "account_id": "acct-9",
        "side": "BUY",
        "event_type": "new_order",
        "order_id": "ord-1",
        "quantity": 100,
        "price": 190.2,
        "order_type": "LIMIT",
        "metadata": {},
    }
    resp = client.post("/events", json=payload, headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["accepted"] is True
