from __future__ import annotations

from collections import deque
from datetime import date

from src.common.schemas import Alert


class AlertService:
    def __init__(self) -> None:
        self.alerts: deque[Alert] = deque(maxlen=20_000)
        self.seen_keys: set[str] = set()

    def _dedup_key(self, alert: Alert) -> str:
        d = alert.ts.date().isoformat()
        return f"{alert.pattern}:{alert.account_id}:{alert.symbol}:{d}"

    def ingest(self, alerts: list[Alert]) -> list[Alert]:
        accepted: list[Alert] = []
        for alert in alerts:
            key = self._dedup_key(alert)
            if key in self.seen_keys:
                continue
            self.seen_keys.add(key)
            self.alerts.appendleft(alert)
            accepted.append(alert)
        self._cleanup_old_keys(date.today())
        return accepted

    def list_alerts(self, limit: int = 100) -> list[Alert]:
        return list(self.alerts)[:limit]

    def _cleanup_old_keys(self, _today: date) -> None:
        # Keep dedup simple for MVP. A production system should use Redis TTL.
        if len(self.seen_keys) > 100_000:
            self.seen_keys = set(list(self.seen_keys)[-50_000:])
