from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.common.schemas import Alert, MarketEvent


def _as_utc(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def collect_related_trades(events: list[MarketEvent], account_id: str, symbol: str, pivot_ts: datetime, days: int = 3) -> list[MarketEvent]:
    pivot = _as_utc(pivot_ts)
    start = pivot - timedelta(days=days)
    end = pivot + timedelta(days=days)
    return [
        e
        for e in events
        if e.account_id == account_id
        and e.symbol == symbol
        and start <= _as_utc(e.ts) <= end
        and e.event_type in {"trade", "fill"}
    ]


def link_prior_alerts(alerts: list[Alert], account_id: str, symbol: str) -> list[Alert]:
    return [a for a in alerts if a.account_id == account_id and a.symbol == symbol]


def summarize_evidence(alert: Alert, related_events: list[MarketEvent], prior_alerts: list[Alert]) -> dict[str, float | int | str]:
    pnl_proxy = 0.0
    for e in related_events:
        pnl_proxy += e.quantity * e.price if e.side == "SELL" else -e.quantity * e.price
    return {
        "alert_id": alert.alert_id,
        "related_trade_count": len(related_events),
        "prior_alert_count": len(prior_alerts),
        "pnl_proxy": round(pnl_proxy, 2),
    }
