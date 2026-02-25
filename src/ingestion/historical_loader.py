from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.common.schemas import MarketEvent


REQUIRED_COLUMNS = {
    "ts",
    "venue",
    "asset_class",
    "symbol",
    "account_id",
    "side",
    "event_type",
    "quantity",
    "price",
}


def load_historical_events(path: str | Path) -> list[MarketEvent]:
    path = Path(path)
    if path.suffix.lower() == ".parquet":
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path)

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    events: list[MarketEvent] = []
    for i, row in df.iterrows():
        ts = row["ts"]
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        events.append(
            MarketEvent(
                event_id=str(row.get("event_id") or f"hist-{i}"),
                ts=ts,
                venue=str(row["venue"]),
                asset_class=str(row["asset_class"]),
                symbol=str(row["symbol"]),
                account_id=str(row["account_id"]),
                side=str(row["side"]),
                event_type=str(row["event_type"]),
                order_id=str(row.get("order_id")) if row.get("order_id") else None,
                trade_id=str(row.get("trade_id")) if row.get("trade_id") else None,
                counterparty_account_id=str(row.get("counterparty_account_id")) if row.get("counterparty_account_id") else None,
                quantity=float(row["quantity"]),
                price=float(row["price"]),
                order_type=str(row.get("order_type") or "LIMIT"),
                metadata=dict(row.get("metadata") or {}),
            )
        )
    return events
