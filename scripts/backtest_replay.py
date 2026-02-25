from __future__ import annotations

import argparse
import json
import time

import requests


def replay(path: str, api_url: str, speed: float = 1.0) -> dict[str, int]:
    with open(path, "r", encoding="utf-8") as f:
        rows = json.load(f)

    sent = 0
    alerts = 0
    for row in rows:
        resp = requests.post(f"{api_url}/events", json=row, timeout=10)
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
    args = parser.parse_args()

    summary = replay(args.input, args.api_url, args.speed)
    print(json.dumps(summary, indent=2))
