from datetime import datetime, timedelta, timezone

from src.common.schemas import MarketEvent
from src.detection.rules.engine import RuleEngine


def mk_event(**overrides):
    base = {
        "event_id": "e1",
        "ts": datetime.now(timezone.utc),
        "venue": "BINANCE",
        "asset_class": "crypto",
        "symbol": "ABC",
        "account_id": "acct-1",
        "side": "BUY",
        "event_type": "trade",
        "order_id": "o1",
        "quantity": 100.0,
        "price": 10.0,
        "order_type": "LIMIT",
        "metadata": {},
    }
    base.update(overrides)
    return MarketEvent(**base)


def test_pump_dump_rule_triggers_distribution_phase() -> None:
    engine = RuleEngine()
    now = datetime.now(timezone.utc)

    # Accumulation phase
    for i in range(5):
        engine.process(
            mk_event(
                event_id=f"b{i}",
                ts=now + timedelta(seconds=i),
                side="BUY",
                quantity=500,
                metadata={"social_mentions_spike": False},
            )
        )

    # Distribution with spike context
    alerts = engine.process(
        mk_event(
            event_id="sell-1",
            ts=now + timedelta(seconds=20),
            side="SELL",
            quantity=1500,
            metadata={"social_mentions_spike": True, "price_change_24h": 0.62, "volume_multiple": 4.0},
        )
    )

    assert any(a.pattern == "pump_and_dump" for a in alerts)
