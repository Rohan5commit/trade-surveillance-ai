from datetime import datetime, timedelta, timezone

from src.common.schemas import MarketEvent
from src.detection.rules.engine import RuleEngine


def mk_event(**overrides):
    base = {
        "event_id": "e1",
        "ts": datetime.now(timezone.utc),
        "venue": "NASDAQ",
        "asset_class": "equity",
        "symbol": "AAPL",
        "account_id": "acct-1",
        "side": "BUY",
        "event_type": "new_order",
        "order_id": "o1",
        "quantity": 100.0,
        "price": 100.0,
        "order_type": "LIMIT",
        "metadata": {},
    }
    base.update(overrides)
    return MarketEvent(**base)


def test_spoofing_rule_triggers() -> None:
    engine = RuleEngine()
    now = datetime.now(timezone.utc)

    # Build baseline average size around 100
    for i in range(10):
        engine.process(mk_event(event_id=f"b{i}", order_id=f"b{i}", ts=now + timedelta(milliseconds=i), quantity=100))

    large_order = mk_event(event_id="l1", order_id="large", ts=now + timedelta(seconds=1), quantity=1000, side="BUY")
    engine.process(large_order)

    fill = mk_event(
        event_id="f1",
        event_type="fill",
        order_id="fill-order",
        side="SELL",
        ts=now + timedelta(seconds=4),
        quantity=10,
    )
    engine.process(fill)

    cancel = mk_event(event_id="c1", event_type="cancel", order_id="large", ts=now + timedelta(seconds=5), quantity=1000)
    alerts = engine.process(cancel)

    assert any(a.pattern == "spoofing" for a in alerts)
