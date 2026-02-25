from __future__ import annotations

from datetime import timedelta
import uuid

from src.common.schemas import Alert, MarketEvent


class CrossMarketDetector:
    """Detect cross-asset and options-equity manipulation patterns."""

    RELATED_INSTRUMENTS = {
        "SPY": {"ES", "SPX"},
        "ES": {"SPY", "SPX"},
        "SPX": {"SPY", "ES"},
    }

    def __init__(self) -> None:
        self.recent_by_account: dict[str, list[MarketEvent]] = {}

    def process(self, event: MarketEvent) -> list[Alert]:
        events = self.recent_by_account.setdefault(event.account_id, [])
        events.append(event)
        # keep only short horizon for CEP-style checks
        cutoff = event.ts - timedelta(minutes=10)
        self.recent_by_account[event.account_id] = [e for e in events if e.ts >= cutoff]

        alerts: list[Alert] = []
        alerts.extend(self._cross_asset_spoofing(event))
        alerts.extend(self._options_equity_pinning(event))
        return alerts

    def _cross_asset_spoofing(self, event: MarketEvent) -> list[Alert]:
        if not bool(event.metadata.get("spoofing_signal", False)):
            return []

        related = self.RELATED_INSTRUMENTS.get(event.symbol, set())
        if not related:
            return []

        recent = self.recent_by_account.get(event.account_id, [])
        for other in reversed(recent):
            if other.symbol in related and other.event_type in {"trade", "fill"}:
                return [
                    Alert(
                        alert_id=str(uuid.uuid4()),
                        ts=event.ts,
                        detector="rules",
                        pattern="cross_asset_spoofing",
                        account_id=event.account_id,
                        symbol=event.symbol,
                        severity="high",
                        score=0.86,
                        reason="Spoofing signal in one instrument with concurrent trading in related market.",
                        evidence={
                            "source_symbol": event.symbol,
                            "related_symbol": other.symbol,
                            "delta_seconds": round((event.ts - other.ts).total_seconds(), 3),
                        },
                    )
                ]
        return []

    def _options_equity_pinning(self, event: MarketEvent) -> list[Alert]:
        if event.asset_class != "equity":
            return []

        option_gamma_pressure = float(event.metadata.get("option_gamma_pressure", 0.0))
        near_expiry = bool(event.metadata.get("near_expiry", False))
        strike_distance = float(event.metadata.get("strike_distance_pct", 1.0))
        if near_expiry and option_gamma_pressure > 0.8 and strike_distance < 0.005:
            return [
                Alert(
                    alert_id=str(uuid.uuid4()),
                    ts=event.ts,
                    detector="rules",
                    pattern="options_equity_manipulation",
                    account_id=event.account_id,
                    symbol=event.symbol,
                    severity="medium",
                    score=0.78,
                    reason="Underlying appears pinned near strike under elevated near-expiry option pressure.",
                    evidence={
                        "gamma_pressure": round(option_gamma_pressure, 4),
                        "strike_distance_pct": round(strike_distance, 5),
                    },
                )
            ]
        return []
