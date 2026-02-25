from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import random
import sys
import time
import uuid

import requests


def _event(
    *,
    ts: datetime,
    account_id: str,
    symbol: str,
    side: str,
    event_type: str,
    quantity: float,
    price: float,
    order_id: str | None = None,
    trade_id: str | None = None,
    counterparty_account_id: str | None = None,
    venue: str = "SIM",
    asset_class: str = "equity",
    metadata: dict | None = None,
) -> dict:
    return {
        "event_id": str(uuid.uuid4()),
        "ts": ts.isoformat(),
        "venue": venue,
        "asset_class": asset_class,
        "symbol": symbol,
        "account_id": account_id,
        "side": side,
        "event_type": event_type,
        "order_id": order_id,
        "trade_id": trade_id,
        "counterparty_account_id": counterparty_account_id,
        "quantity": float(quantity),
        "price": float(price),
        "order_type": "LIMIT" if event_type != "fill" else "MARKET",
        "metadata": metadata or {},
    }


def build_suspicious_event_batch(start: datetime) -> list[dict]:
    rows: list[dict] = []
    ts = start

    # Baseline orders to set normal account behavior.
    for _ in range(20):
        rows.append(
            _event(
                ts=ts,
                account_id="acct-spoof-1",
                symbol="SPY",
                side="BUY",
                event_type="new_order",
                quantity=20,
                price=499.90,
                order_id=f"baseline-{uuid.uuid4()}",
            )
        )
        ts += timedelta(milliseconds=30)

    # Layering burst.
    layer_ids = [f"layer-{i}" for i in range(6)]
    layer_prices = [500.01, 500.02, 500.03, 500.04, 500.05, 500.06]
    for oid, px in zip(layer_ids, layer_prices):
        rows.append(
            _event(
                ts=ts,
                account_id="acct-layer-1",
                symbol="SPY",
                side="BUY",
                event_type="new_order",
                quantity=1200,
                price=px,
                order_id=oid,
            )
        )
        ts += timedelta(milliseconds=25)
    for oid, px in zip(layer_ids, layer_prices):
        rows.append(
            _event(
                ts=ts,
                account_id="acct-layer-1",
                symbol="SPY",
                side="BUY",
                event_type="cancel",
                quantity=1200,
                price=px,
                order_id=oid,
            )
        )
        ts += timedelta(milliseconds=25)

    # Spoofing signature: large order, opposite-side fill, fast cancel.
    spoof_order_id = "spoof-order-1"
    rows.append(
        _event(
            ts=ts,
            account_id="acct-spoof-1",
            symbol="SPY",
            side="BUY",
            event_type="new_order",
            quantity=10000,
            price=499.70,
            order_id=spoof_order_id,
            metadata={"spoofing_signal": True},
        )
    )
    ts += timedelta(seconds=4)
    rows.append(
        _event(
            ts=ts,
            account_id="acct-spoof-1",
            symbol="ES",
            side="SELL",
            event_type="fill",
            quantity=100,
            price=5000.0,
            order_id="es-fill-1",
            metadata={"spoofing_signal": True},
            asset_class="future",
        )
    )
    ts += timedelta(seconds=1)
    rows.append(
        _event(
            ts=ts,
            account_id="acct-spoof-1",
            symbol="SPY",
            side="BUY",
            event_type="cancel",
            quantity=10000,
            price=499.70,
            order_id=spoof_order_id,
            metadata={"spoofing_signal": True},
        )
    )
    ts += timedelta(milliseconds=100)

    # Self wash trade.
    rows.append(
        _event(
            ts=ts,
            account_id="acct-wash-1",
            symbol="AAPL",
            side="BUY",
            event_type="trade",
            quantity=900,
            price=191.2,
            trade_id="wash-self-1",
            counterparty_account_id="acct-wash-1",
        )
    )
    ts += timedelta(milliseconds=50)

    # Circular wash ring.
    rows.append(
        _event(
            ts=ts,
            account_id="ring-a",
            symbol="MSFT",
            side="BUY",
            event_type="trade",
            quantity=500,
            price=405.2,
            trade_id="ring-1",
            counterparty_account_id="ring-b",
        )
    )
    ts += timedelta(milliseconds=50)
    rows.append(
        _event(
            ts=ts,
            account_id="ring-b",
            symbol="MSFT",
            side="BUY",
            event_type="trade",
            quantity=500,
            price=405.3,
            trade_id="ring-2",
            counterparty_account_id="ring-c",
        )
    )
    ts += timedelta(milliseconds=50)
    rows.append(
        _event(
            ts=ts,
            account_id="ring-c",
            symbol="MSFT",
            side="BUY",
            event_type="trade",
            quantity=500,
            price=405.4,
            trade_id="ring-3",
            counterparty_account_id="ring-a",
        )
    )
    ts += timedelta(milliseconds=100)

    # Quote stuffing profile.
    for i in range(125):
        rows.append(
            _event(
                ts=ts + timedelta(milliseconds=i * 6),
                account_id="acct-qs-1",
                symbol="NVDA",
                side="SELL",
                event_type="cancel",
                quantity=50,
                price=800.0 + (i % 4) * 0.01,
                order_id=f"qs-{i}",
                metadata={"latency_impact_ms": 4.0},
            )
        )
    ts += timedelta(seconds=1)

    # Pump-and-dump distribution phase signal.
    rows.append(
        _event(
            ts=ts,
            account_id="acct-pnd-1",
            symbol="XYZ",
            side="BUY",
            event_type="trade",
            quantity=2000,
            price=12.0,
            trade_id="pnd-buy-1",
            counterparty_account_id="acct-maker",
            metadata={"social_mentions_spike": True, "price_change_24h": 0.62, "volume_multiple": 4.2},
        )
    )
    ts += timedelta(milliseconds=100)
    rows.append(
        _event(
            ts=ts,
            account_id="acct-pnd-1",
            symbol="XYZ",
            side="SELL",
            event_type="trade",
            quantity=1200,
            price=16.4,
            trade_id="pnd-sell-1",
            counterparty_account_id="acct-maker",
            metadata={"social_mentions_spike": True, "price_change_24h": 0.62, "volume_multiple": 4.2},
        )
    )
    ts += timedelta(milliseconds=100)

    # Options-equity manipulation signal.
    rows.append(
        _event(
            ts=ts,
            account_id="acct-opt-1",
            symbol="AAPL",
            side="BUY",
            event_type="fill",
            quantity=800,
            price=191.0,
            order_id="opt-fill-1",
            metadata={"near_expiry": True, "option_gamma_pressure": 0.91, "strike_distance_pct": 0.003},
        )
    )

    return rows


def add_background_flow(rows: list[dict], start: datetime, target_total: int) -> list[dict]:
    if len(rows) >= target_total:
        return rows[:target_total]

    ts = start + timedelta(seconds=10)
    symbols = ["AAPL", "MSFT", "SPY", "NVDA"]
    for _ in range(target_total - len(rows)):
        event_type = random.choice(["new_order", "fill", "trade", "cancel"])
        rows.append(
            _event(
                ts=ts,
                account_id=f"acct-bg-{random.randint(1, 12)}",
                symbol=random.choice(symbols),
                side=random.choice(["BUY", "SELL"]),
                event_type=event_type,
                quantity=random.randint(10, 600),
                price=round(random.uniform(80, 550), 2),
                order_id=f"bg-order-{uuid.uuid4()}",
                trade_id=f"bg-trade-{uuid.uuid4()}" if event_type == "trade" else None,
                counterparty_account_id="acct-mm" if event_type == "trade" else None,
            )
        )
        ts += timedelta(milliseconds=15)
    return rows


def wait_for_api(api_url: str, timeout_seconds: int) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            resp = requests.get(f"{api_url}/health", timeout=3)
            if resp.status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(1)
    raise RuntimeError(f"API not healthy within {timeout_seconds}s: {api_url}")


def bootstrap_api_key(api_url: str) -> str:
    email = f"demo-{uuid.uuid4().hex[:12]}@example.com"
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
        json={"name": "simulator"},
        timeout=10,
    )
    key_resp.raise_for_status()
    return key_resp.json()["api_key"]


def run(api_url: str, events: int, api_key: str | None, bootstrap_auth: bool, wait_ready_seconds: int) -> dict:
    wait_for_api(api_url, timeout_seconds=wait_ready_seconds)

    resolved_key = api_key
    if not resolved_key and bootstrap_auth:
        resolved_key = bootstrap_api_key(api_url)

    headers = {"x-api-key": resolved_key} if resolved_key else {}

    start = datetime.now(timezone.utc)
    rows = build_suspicious_event_batch(start)
    rows = add_background_flow(rows, start, events)

    sent = 0
    generated_alerts = 0
    failures = 0
    for row in rows:
        resp = requests.post(f"{api_url}/events", json=row, headers=headers, timeout=10)
        if resp.status_code != 200:
            failures += 1
            continue
        payload = resp.json()
        generated_alerts += int(payload.get("generated_alerts", 0))
        sent += 1

    alerts_resp = requests.get(f"{api_url}/alerts?limit=200", headers=headers, timeout=10)
    alerts_resp.raise_for_status()
    alerts = alerts_resp.json()

    pattern_counts: dict[str, int] = {}
    for item in alerts:
        pattern = str(item.get("pattern", "unknown"))
        pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

    return {
        "events_requested": events,
        "events_sent": sent,
        "post_failures": failures,
        "alerts_in_store": len(alerts),
        "alerts_generated_during_run": generated_alerts,
        "alert_patterns": pattern_counts,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed API with synthetic suspicious trading activity")
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--events", type=int, default=800)
    parser.add_argument("--api-key", default="")
    parser.add_argument("--bootstrap-auth", action="store_true")
    parser.add_argument("--wait-ready-seconds", type=int, default=60)
    args = parser.parse_args()

    try:
        summary = run(
            api_url=args.api_url.rstrip("/"),
            events=max(50, args.events),
            api_key=args.api_key.strip() or None,
            bootstrap_auth=args.bootstrap_auth,
            wait_ready_seconds=max(1, args.wait_ready_seconds),
        )
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        sys.exit(1)

    print(json.dumps({"ok": True, **summary}, indent=2))
