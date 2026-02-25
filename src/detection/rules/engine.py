from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from statistics import mean
import uuid

from src.common.schemas import Alert, MarketEvent


@dataclass
class OrderState:
    order_id: str
    ts: datetime
    side: str
    quantity: float
    price: float


class RuleEngine:
    def __init__(self) -> None:
        self.open_orders: dict[str, dict[str, OrderState]] = defaultdict(dict)
        self.order_sizes: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=500))
        self.recent_actions: dict[str, deque[MarketEvent]] = defaultdict(lambda: deque(maxlen=5_000))
        self.recent_fills: dict[str, deque[MarketEvent]] = defaultdict(lambda: deque(maxlen=500))
        self.session_volume: dict[str, float] = defaultdict(float)
        self.last_prices: dict[str, deque[tuple[datetime, float]]] = defaultdict(lambda: deque(maxlen=2_000))
        self.account_symbol_side_volume: dict[tuple[str, str, str], float] = defaultdict(float)
        self.account_symbol_total_volume: dict[tuple[str, str], deque[float]] = defaultdict(lambda: deque(maxlen=250))

    def process(self, event: MarketEvent) -> list[Alert]:
        alerts: list[Alert] = []
        self.recent_actions[event.account_id].append(event)

        if event.event_type == "new_order" and event.order_id:
            self.open_orders[event.account_id][event.order_id] = OrderState(
                order_id=event.order_id,
                ts=event.ts,
                side=event.side,
                quantity=event.quantity,
                price=event.price,
            )
            self.order_sizes[event.account_id].append(event.quantity)

        if event.event_type == "fill":
            self.recent_fills[event.account_id].append(event)
            self.session_volume[event.symbol] += event.quantity
            self.last_prices[event.symbol].append((event.ts, event.price))
            self.account_symbol_side_volume[(event.account_id, event.symbol, event.side)] += event.quantity
            self.account_symbol_total_volume[(event.account_id, event.symbol)].append(event.quantity)

        if event.event_type == "trade":
            self.session_volume[event.symbol] += event.quantity
            self.last_prices[event.symbol].append((event.ts, event.price))
            self.account_symbol_side_volume[(event.account_id, event.symbol, event.side)] += event.quantity
            self.account_symbol_total_volume[(event.account_id, event.symbol)].append(event.quantity)
            alerts.extend(self._detect_wash_trade(event))

        if event.event_type == "cancel" and event.order_id:
            alerts.extend(self._detect_spoofing(event))

        alerts.extend(self._detect_quote_stuffing(event))
        alerts.extend(self._detect_marking_the_close(event))
        alerts.extend(self._detect_pump_and_dump(event))
        alerts.extend(self._detect_pre_announcement_trading(event))
        return alerts

    def _detect_spoofing(self, cancel_event: MarketEvent) -> list[Alert]:
        order = self.open_orders[cancel_event.account_id].pop(cancel_event.order_id, None)
        if not order:
            return []

        age_seconds = (cancel_event.ts - order.ts).total_seconds()
        avg_size = mean(self.order_sizes[cancel_event.account_id]) if self.order_sizes[cancel_event.account_id] else order.quantity
        if avg_size <= 0:
            avg_size = 1.0

        if order.quantity < 5 * avg_size or age_seconds > 10:
            return []

        opposite_side = "BUY" if order.side == "SELL" else "SELL"
        for fill in reversed(self.recent_fills[cancel_event.account_id]):
            dt = (cancel_event.ts - fill.ts).total_seconds()
            if dt > 10:
                break
            if fill.side == opposite_side:
                return [
                    Alert(
                        alert_id=str(uuid.uuid4()),
                        ts=cancel_event.ts,
                        detector="rules",
                        pattern="spoofing",
                        account_id=cancel_event.account_id,
                        symbol=cancel_event.symbol,
                        severity="high",
                        score=0.92,
                        reason="Large order canceled quickly followed by opposite-side execution.",
                        evidence={
                            "order_size": round(order.quantity, 2),
                            "avg_order_size": round(avg_size, 2),
                            "cancel_age_seconds": round(age_seconds, 3),
                            "opposite_fill_seconds": round(dt, 3),
                        },
                    )
                ]
        return []

    def _detect_wash_trade(self, trade_event: MarketEvent) -> list[Alert]:
        if not trade_event.counterparty_account_id:
            return []

        if trade_event.counterparty_account_id == trade_event.account_id:
            return [
                Alert(
                    alert_id=str(uuid.uuid4()),
                    ts=trade_event.ts,
                    detector="rules",
                    pattern="wash_trade",
                    account_id=trade_event.account_id,
                    symbol=trade_event.symbol,
                    severity="critical",
                    score=0.98,
                    reason="Trade executed against same account.",
                    evidence={
                        "quantity": trade_event.quantity,
                        "price": trade_event.price,
                    },
                )
            ]

        return []

    def _detect_quote_stuffing(self, event: MarketEvent) -> list[Alert]:
        actions = self.recent_actions[event.account_id]
        one_sec_ago = event.ts - timedelta(seconds=1)
        five_sec_ago = event.ts - timedelta(seconds=5)

        per_second = sum(1 for e in actions if e.ts >= one_sec_ago and e.event_type in {"new_order", "cancel"})
        recent = [e for e in actions if e.ts >= five_sec_ago and e.event_type in {"new_order", "cancel"}]
        cancels = sum(1 for e in recent if e.event_type == "cancel")
        ratio = cancels / len(recent) if recent else 0

        if per_second > 100 and ratio > 0.95:
            return [
                Alert(
                    alert_id=str(uuid.uuid4()),
                    ts=event.ts,
                    detector="rules",
                    pattern="quote_stuffing",
                    account_id=event.account_id,
                    symbol=event.symbol,
                    severity="high",
                    score=0.9,
                    reason="Sustained very high order/cancel rate with extreme cancellation ratio.",
                    evidence={"orders_per_second": per_second, "cancel_ratio_5s": round(ratio, 3)},
                )
            ]
        return []

    def _detect_marking_the_close(self, event: MarketEvent) -> list[Alert]:
        ts_utc = event.ts.astimezone(timezone.utc)
        if ts_utc.hour != 20 and ts_utc.hour != 21:
            return []

        # Approximate US close window at 20:50-21:00 UTC for regular sessions.
        if not (ts_utc.minute >= 50 or ts_utc.hour == 21 and ts_utc.minute == 0):
            return []

        if event.event_type not in {"fill", "trade"}:
            return []

        typical_10m_volume = max(self.session_volume[event.symbol] * 0.1, 1.0)
        price_points = self.last_prices[event.symbol]
        if len(price_points) < 2:
            return []

        first_price = price_points[0][1]
        latest_price = price_points[-1][1]
        if first_price <= 0:
            return []

        move = abs((latest_price - first_price) / first_price)
        if event.quantity > 0.1 * typical_10m_volume and move > 0.02:
            return [
                Alert(
                    alert_id=str(uuid.uuid4()),
                    ts=event.ts,
                    detector="rules",
                    pattern="marking_the_close",
                    account_id=event.account_id,
                    symbol=event.symbol,
                    severity="medium",
                    score=0.74,
                    reason="Large near-close trade with significant short-window price movement.",
                    evidence={
                        "event_quantity": event.quantity,
                        "approx_typical_10m_volume": round(typical_10m_volume, 2),
                        "price_move": round(move, 4),
                    },
                )
            ]
        return []

    def _detect_pump_and_dump(self, event: MarketEvent) -> list[Alert]:
        if event.event_type not in {"trade", "fill"}:
            return []

        mentions_spike = bool(event.metadata.get("social_mentions_spike", False))
        price_change_24h = float(event.metadata.get("price_change_24h", 0.0))
        volume_multiple = float(event.metadata.get("volume_multiple", 1.0))
        if not mentions_spike or price_change_24h < 0.5 or volume_multiple < 3.0:
            return []

        accumulated_buy_volume = self.account_symbol_side_volume[(event.account_id, event.symbol, "BUY")]
        sold_volume = self.account_symbol_side_volume[(event.account_id, event.symbol, "SELL")]
        # Potential distribution phase after accumulation.
        if event.side == "SELL" and accumulated_buy_volume > 0 and sold_volume >= 0.5 * accumulated_buy_volume:
            return [
                Alert(
                    alert_id=str(uuid.uuid4()),
                    ts=event.ts,
                    detector="rules",
                    pattern="pump_and_dump",
                    account_id=event.account_id,
                    symbol=event.symbol,
                    severity="critical",
                    score=0.95,
                    reason="Sell-off during social/price/volume spike after prior accumulation.",
                    evidence={
                        "price_change_24h": round(price_change_24h, 4),
                        "volume_multiple": round(volume_multiple, 2),
                        "buy_volume": round(accumulated_buy_volume, 2),
                        "sell_volume": round(sold_volume, 2),
                    },
                )
            ]
        return []

    def _detect_pre_announcement_trading(self, event: MarketEvent) -> list[Alert]:
        if event.event_type not in {"trade", "fill"}:
            return []

        days_to_event_raw = event.metadata.get("days_to_event")
        if days_to_event_raw is None:
            return []
        days_to_event = int(days_to_event_raw)
        if not (0 <= days_to_event <= 30):
            return []

        key = (event.account_id, event.symbol)
        history = self.account_symbol_total_volume[key]
        avg_vol = mean(history) if history else event.quantity
        if avg_vol <= 0:
            avg_vol = 1.0

        directional_edge = bool(event.metadata.get("direction_matches_event_outcome", False))
        if event.quantity >= 3 * avg_vol and directional_edge:
            return [
                Alert(
                    alert_id=str(uuid.uuid4()),
                    ts=event.ts,
                    detector="rules",
                    pattern="pre_announcement_trading",
                    account_id=event.account_id,
                    symbol=event.symbol,
                    severity="high",
                    score=0.88,
                    reason="Unusually large event-window trade with direction matching announced outcome.",
                    evidence={
                        "days_to_event": days_to_event,
                        "trade_qty": round(event.quantity, 2),
                        "avg_qty": round(avg_vol, 2),
                    },
                )
            ]
        return []
