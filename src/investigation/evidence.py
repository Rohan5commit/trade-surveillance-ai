from __future__ import annotations

from datetime import datetime, timedelta

from src.common.schemas import Alert, MarketEvent


def collect_related_trades(events: list[MarketEvent], account_id: str, symbol: str, pivot_ts: datetime, days: int = 3) -> list[MarketEvent]:
    start = pivot_ts - timedelta(days=days)
    end = pivot_ts + timedelta(days=days)
    return [
        e
        for e in events
        if e.account_id == account_id and e.symbol == symbol and start <= e.ts <= end and e.event_type in {"trade", "fill"}
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
