from __future__ import annotations

import argparse
import json
import time
import uuid

import requests


def _bootstrap_api_key(api_url: str) -> str:
    email = f"backtest-{uuid.uuid4().hex[:12]}@example.com"
    password = "DemoPass!12345"

    register_resp = requests.post(
        f"{api_url}/auth/register",
        json={"email": email, "password": password},
        timeout=10,
    )
    if register_resp.status_code not in {200, 409}:
        raise RuntimeError(f"register failed: {register_resp.status_code} {register_resp.text}")

    token_resp = requests.post(
        f"{api_url}/auth/token",
        json={"email": email, "password": password},
        timeout=10,
    )
    token_resp.raise_for_status()
    token = token_resp.json()["access_token"]

    key_resp = requests.post(
        f"{api_url}/auth/api-keys",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "backtest"},
        timeout=10,
    )
    key_resp.raise_for_status()
    return key_resp.json()["api_key"]


def replay(path: str, api_url: str, speed: float = 1.0, api_key: str = "", bootstrap_auth: bool = False) -> dict[str, int]:
    with open(path, "r", encoding="utf-8") as f:
        rows = json.load(f)

    resolved_api_key = api_key.strip()
    if not resolved_api_key and bootstrap_auth:
        resolved_api_key = _bootstrap_api_key(api_url)
    headers = {"x-api-key": resolved_api_key} if resolved_api_key else {}

    sent = 0
    alerts = 0
    for row in rows:
        resp = requests.post(f"{api_url}/events", json=row, headers=headers, timeout=10)
        resp.raise_for_status()
        body = resp.json()
        sent += 1
        alerts += int(body.get("generated_alerts", 0))
        time.sleep(max(0.0, 0.01 / max(speed, 1e-6)))

    return {"events_sent": sent, "alerts_generated": alerts}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Replay historical events against surveillance API")
    parser.add_argument("--input", required=True, help="JSON array of MarketEvent payloads")
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--api-key", default="")
    parser.add_argument("--bootstrap-auth", action="store_true")
    args = parser.parse_args()

    summary = replay(args.input, args.api_url, args.speed, api_key=args.api_key, bootstrap_auth=args.bootstrap_auth)
    print(json.dumps(summary, indent=2))
