from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from src.api.main import app


def _create_tenant(client: TestClient) -> dict[str, str]:
    email = f"tenant-{uuid.uuid4().hex[:10]}@example.com"
    password = "TenantPass!12345"

    register = client.post("/auth/register", json={"email": email, "password": password})
    assert register.status_code == 200

    token = client.post("/auth/token", json={"email": email, "password": password})
    assert token.status_code == 200
    access_token = token.json()["access_token"]

    created = client.post(
        "/auth/api-keys",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"name": "tenant-key"},
    )
    assert created.status_code == 200

    return {
        "token": access_token,
        "api_key": created.json()["api_key"],
    }


def test_tenant_case_isolation() -> None:
    client = TestClient(app)

    t1 = _create_tenant(client)
    t2 = _create_tenant(client)

    c1 = client.post(
        "/cases",
        json={
            "alert_id": "iso-a1",
            "account_id": "acct-a",
            "symbol": "AAPL",
            "severity": "high",
            "summary": "tenant-a-case",
        },
        headers={"x-api-key": t1["api_key"]},
    )
    assert c1.status_code == 200

    c2 = client.post(
        "/cases",
        json={
            "alert_id": "iso-b1",
            "account_id": "acct-b",
            "symbol": "MSFT",
            "severity": "medium",
            "summary": "tenant-b-case",
        },
        headers={"x-api-key": t2["api_key"]},
    )
    assert c2.status_code == 200

    t1_cases = client.get("/cases", headers={"x-api-key": t1["api_key"]})
    t2_cases = client.get("/cases", headers={"x-api-key": t2["api_key"]})
    assert t1_cases.status_code == 200
    assert t2_cases.status_code == 200

    t1_summaries = {row["summary"] for row in t1_cases.json()}
    t2_summaries = {row["summary"] for row in t2_cases.json()}

    assert "tenant-a-case" in t1_summaries
    assert "tenant-b-case" not in t1_summaries
    assert "tenant-b-case" in t2_summaries
    assert "tenant-a-case" not in t2_summaries
