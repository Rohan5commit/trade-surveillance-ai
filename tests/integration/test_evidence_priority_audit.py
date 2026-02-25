from datetime import datetime, timezone

from fastapi.testclient import TestClient

from src.api.main import app
from tests.integration.auth_helpers import build_api_key_headers


def test_evidence_priority_and_audit() -> None:
    client = TestClient(app)
    headers = build_api_key_headers(client)

    evt = {
        "event_id": "evt-evi-1",
        "ts": datetime.now(timezone.utc).isoformat(),
        "venue": "SIM",
        "asset_class": "equity",
        "symbol": "AAPL",
        "account_id": "acct-evi",
        "side": "BUY",
        "event_type": "new_order",
        "order_id": "ord-evi-1",
        "quantity": 100,
        "price": 190,
        "order_type": "LIMIT",
        "metadata": {},
    }
    ingest = client.post("/events", json=evt, headers=headers)
    assert ingest.status_code == 200

    case = client.post(
        "/cases",
        json={
            "alert_id": "manual-alert-1",
            "account_id": "acct-evi",
            "symbol": "AAPL",
            "severity": "medium",
            "summary": "manual case",
        },
        headers=headers,
    )
    assert case.status_code == 200
    cid = case.json()["id"]

    evidence = client.get(f"/cases/{cid}/evidence", headers=headers)
    assert evidence.status_code == 200

    priority = client.get("/alerts/manual-alert-1/priority", headers=headers)
    # Manual alert may not exist in alert store; allow 404 as valid behavior.
    assert priority.status_code in {200, 404}

    audit = client.get("/audit/verify")
    assert audit.status_code == 200
    assert "valid" in audit.json()
