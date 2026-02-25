from __future__ import annotations

from datetime import datetime, timezone
import uuid

from locust import HttpUser, between, task


class SurveillanceUser(HttpUser):
    wait_time = between(0.01, 0.05)

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
        self.client.post("/events", json=payload)

    @task(1)
    def fetch_alerts(self):
        self.client.get("/alerts")
