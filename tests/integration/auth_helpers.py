from __future__ import annotations

import uuid

from fastapi.testclient import TestClient


def build_api_key_headers(client: TestClient) -> dict[str, str]:
    email = f"pytest-{uuid.uuid4().hex[:12]}@example.com"
    password = "PytestPass!12345"

    register = client.post("/auth/register", json={"email": email, "password": password})
    assert register.status_code in {200, 409}

    token = client.post("/auth/token", json={"email": email, "password": password})
    assert token.status_code == 200
    access_token = token.json()["access_token"]

    api_key = client.post(
        "/auth/api-keys",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"name": "pytest"},
    )
    assert api_key.status_code == 200
    return {"x-api-key": api_key.json()["api_key"]}
