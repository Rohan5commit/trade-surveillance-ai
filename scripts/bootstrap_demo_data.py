from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import random


def generate_events(n: int = 500) -> list[dict]:
    now = datetime.now(timezone.utc)
    events = []
    for i in range(n):
        ts = now + timedelta(milliseconds=i * 20)
        event_type = random.choice(["new_order", "cancel", "fill", "trade"])
        events.append(
            {
                "event_id": f"evt-{i}",
                "ts": ts.isoformat(),
                "venue": random.choice(["NASDAQ", "NYSE", "BINANCE"]),
                "asset_class": random.choice(["equity", "crypto", "future"]),
                "symbol": random.choice(["AAPL", "MSFT", "BTCUSDT"]),
                "account_id": random.choice(["acct-1", "acct-2", "acct-3"]),
                "side": random.choice(["BUY", "SELL"]),
                "event_type": event_type,
                "order_id": f"ord-{i // 2}",
                "trade_id": f"trd-{i}" if event_type == "trade" else None,
                "counterparty_account_id": "acct-1" if event_type == "trade" and i % 200 == 0 else "acct-x",
                "quantity": float(random.randint(1, 10_000)),
                "price": round(random.uniform(10, 300), 2),
                "order_type": "LIMIT",
                "metadata": {},
            }
        )
    return events


if __name__ == "__main__":
    print(json.dumps(generate_events(), indent=2))
