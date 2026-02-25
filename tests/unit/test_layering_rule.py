from datetime import datetime, timedelta, timezone

from src.common.schemas import MarketEvent
from src.detection.rules.engine import RuleEngine


def mk(i: int, event_type: str = "new_order") -> MarketEvent:
    return MarketEvent(
        event_id=f"e-{i}",
        ts=datetime.now(timezone.utc) + timedelta(seconds=i),
        venue="SIM",
        asset_class="equity",
        symbol="AAPL",
        account_id="acct-layer",
        side="BUY",
        event_type=event_type,
        order_id=f"ord-{i}",
        quantity=100 + i,
        price=190.0 + i * 0.01,
        order_type="LIMIT",
        metadata={},
    )


def test_layering_triggers() -> None:
    engine = RuleEngine()
    for i in range(6):
        engine.process(mk(i, "new_order"))
    alerts = []
    for i in range(6, 12):
        alerts.extend(engine.process(mk(i, "cancel")))
    assert any(a.pattern == "layering" for a in alerts)
