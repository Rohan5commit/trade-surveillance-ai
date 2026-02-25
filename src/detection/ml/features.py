from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
import numpy as np

from src.common.schemas import MarketEvent


FEATURE_NAMES = [
    "order_count",
    "cancel_count",
    "fill_count",
    "avg_order_size",
    "std_order_size",
    "cancel_to_fill_ratio",
    "time_between_orders_mean",
    "time_between_orders_std",
    "price_distance_from_touch_mean",
    "volume_concentration_herfindahl",
    "order_book_side_imbalance",
    "intraday_volatility",
]


@dataclass
class SessionFeatures:
    account_id: str
    symbol: str
    vector: np.ndarray


def _safe_std(values: list[float]) -> float:
    return float(np.std(values)) if len(values) > 1 else 0.0


def extract_session_features(events: list[MarketEvent]) -> SessionFeatures:
    if not events:
        raise ValueError("events must not be empty")

    events = sorted(events, key=lambda e: e.ts)
    account_id = events[0].account_id
    symbol = events[0].symbol

    order_sizes = [e.quantity for e in events if e.event_type == "new_order"]
    order_count = len(order_sizes)
    cancel_count = sum(1 for e in events if e.event_type == "cancel")
    fill_count = sum(1 for e in events if e.event_type in {"fill", "trade"})

    order_times = [e.ts for e in events if e.event_type == "new_order"]
    deltas = []
    for i in range(1, len(order_times)):
        dt = (order_times[i] - order_times[i - 1]).total_seconds()
        deltas.append(dt)

    prices = [e.price for e in events if e.event_type in {"fill", "trade"}]
    returns = []
    for i in range(1, len(prices)):
        if prices[i - 1] > 0:
            returns.append((prices[i] - prices[i - 1]) / prices[i - 1])

    buy_qty = sum(e.quantity for e in events if e.side == "BUY")
    sell_qty = sum(e.quantity for e in events if e.side == "SELL")
    imbalance = (buy_qty - sell_qty) / max(buy_qty + sell_qty, 1.0)

    vol_by_symbol = defaultdict(float)
    total_vol = 0.0
    for e in events:
        if e.event_type in {"fill", "trade"}:
            vol_by_symbol[e.symbol] += e.quantity
            total_vol += e.quantity
    if total_vol > 0:
        hhi = sum((v / total_vol) ** 2 for v in vol_by_symbol.values())
    else:
        hhi = 0.0

    vector = np.array(
        [
            float(order_count),
            float(cancel_count),
            float(fill_count),
            float(np.mean(order_sizes)) if order_sizes else 0.0,
            _safe_std(order_sizes),
            float(cancel_count / max(fill_count, 1)),
            float(np.mean(deltas)) if deltas else 0.0,
            _safe_std(deltas),
            0.0,
            float(hhi),
            float(imbalance),
            float(_safe_std(returns)),
        ],
        dtype=float,
    )

    return SessionFeatures(account_id=account_id, symbol=symbol, vector=vector)
