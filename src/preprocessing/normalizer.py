from __future__ import annotations

from datetime import timezone

from src.common.schemas import MarketEvent


SYMBOL_ALIASES = {
    "AAPL.US": "AAPL",
    "AAPL.NASDAQ": "AAPL",
}


def normalize_event(event: MarketEvent) -> MarketEvent:
    ts = event.ts
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    else:
        ts = ts.astimezone(timezone.utc)

    symbol = SYMBOL_ALIASES.get(event.symbol, event.symbol)

    return event.model_copy(update={"ts": ts, "symbol": symbol})
