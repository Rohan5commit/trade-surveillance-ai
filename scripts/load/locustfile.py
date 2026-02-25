from __future__ import annotations

from datetime import datetime, timezone
import os
import uuid

from gevent.lock import Semaphore
from locust import HttpUser, between, task


_BOOTSTRAP_LOCK = Semaphore()
_SHARED_API_KEY: str = ""
_BOOTSTRAP_ATTEMPTED = False


def _bootstrap_api_key(client) -> str:
    global _SHARED_API_KEY, _BOOTSTRAP_ATTEMPTED
    with _BOOTSTRAP_LOCK:
        if _SHARED_API_KEY:
            return _SHARED_API_KEY
        if _BOOTSTRAP_ATTEMPTED:
            return ""
        _BOOTSTRAP_ATTEMPTED = True

        email = f"locust-{uuid.uuid4().hex[:10]}@example.com"
        password = "DemoPass!12345"
        register = client.post("/auth/register", json={"email": email, "password": password}, name="/auth/register")
        if register.status_code not in {200, 409}:
            return ""

        token = client.post("/auth/token", json={"email": email, "password": password}, name="/auth/token")
        if token.status_code != 200:
            return ""
        bearer = token.json().get("access_token", "")
        if not bearer:
            return ""

        created = client.post(
            "/auth/api-keys",
            headers={"Authorization": f"Bearer {bearer}"},
            json={"name": "locust"},
            name="/auth/api-keys",
        )
        if created.status_code != 200:
            return ""

        _SHARED_API_KEY = created.json().get("api_key", "")
        return _SHARED_API_KEY


class SurveillanceUser(HttpUser):
    wait_time = between(0.01, 0.05)

    def on_start(self) -> None:
        api_key = os.getenv("SURVEILLANCE_API_KEY", "").strip()
        bootstrap_auth = os.getenv("SURVEILLANCE_BOOTSTRAP_AUTH", "0").strip().lower() in {"1", "true", "yes"}

        if not api_key and bootstrap_auth:
            api_key = _bootstrap_api_key(self.client)

        self.headers = {"x-api-key": api_key} if api_key else {}

    @task
    def post_event(self):
        payload = {
            "event_id": str(uuid.uuid4()),
            "ts": datetime.now(timezone.utc).isoformat(),
            "venue": "SIM",
            "asset_class": "equity",
            "symbol": "AAPL",
            "account_id": "load-acct",
            "side": "BUY",
            "event_type": "new_order",
            "order_id": str(uuid.uuid4()),
            "quantity": 100.0,
            "price": 190.0,
            "order_type": "LIMIT",
            "metadata": {},
        }
        self.client.post("/events", json=payload, headers=self.headers)

    @task(1)
    def fetch_alerts(self):
        self.client.get("/alerts", headers=self.headers)
