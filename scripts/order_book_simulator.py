from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json


@dataclass
class SpoofingStrategy:
    account_id: str
    symbol: str

    def execute(self, start_ts: datetime) -> list[dict]:
        return [
            {
                "event_id": "sim-1",
                "ts": start_ts.isoformat(),
                "venue": "SIM",
                "asset_class": "equity",
                "symbol": self.symbol,
                "account_id": self.account_id,
                "side": "BUY",
                "event_type": "new_order",
                "order_id": "sim-order-1",
                "quantity": 10000,
                "price": 99.95,
                "order_type": "LIMIT",
                "metadata": {"spoofing_signal": True},
            },
            {
                "event_id": "sim-2",
                "ts": (start_ts + timedelta(seconds=5)).isoformat(),
                "venue": "SIM",
                "asset_class": "equity",
                "symbol": self.symbol,
                "account_id": self.account_id,
                "side": "SELL",
                "event_type": "fill",
                "order_id": "sim-fill-1",
                "quantity": 100,
                "price": 100.05,
                "order_type": "MARKET",
                "metadata": {},
            },
            {
                "event_id": "sim-3",
                "ts": (start_ts + timedelta(seconds=6)).isoformat(),
                "venue": "SIM",
                "asset_class": "equity",
                "symbol": self.symbol,
                "account_id": self.account_id,
                "side": "BUY",
                "event_type": "cancel",
                "order_id": "sim-order-1",
                "quantity": 10000,
                "price": 99.95,
                "order_type": "LIMIT",
                "metadata": {"spoofing_signal": True},
            },
        ]


if __name__ == "__main__":
    strategy = SpoofingStrategy(account_id="sim-acct", symbol="SPY")
    events = strategy.execute(datetime.now(timezone.utc))
    print(json.dumps(events, indent=2))
