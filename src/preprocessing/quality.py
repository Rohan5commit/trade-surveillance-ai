from __future__ import annotations

from collections import Counter
from datetime import timedelta

from src.common.schemas import MarketEvent


def detect_clock_drift(events: list[MarketEvent], max_skew_seconds: float = 5.0) -> list[str]:
    alerts: list[str] = []
    events = sorted(events, key=lambda e: e.ts)
    for i in range(1, len(events)):
        if events[i].ts < events[i - 1].ts - timedelta(seconds=max_skew_seconds):
            alerts.append(f"clock_drift:{events[i].event_id}")
    return alerts


def detect_duplicates(events: list[MarketEvent]) -> list[str]:
    ids = [e.event_id for e in events]
    counts = Counter(ids)
    return [event_id for event_id, c in counts.items() if c > 1]


def missing_required_fields(events: list[MarketEvent]) -> list[str]:
    missing: list[str] = []
    for event in events:
        if not event.symbol or not event.account_id or event.quantity <= 0 or event.price <= 0:
            missing.append(event.event_id)
    return missing
