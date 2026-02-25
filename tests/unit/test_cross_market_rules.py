from datetime import datetime, timezone

from src.common.schemas import MarketEvent
from src.detection.rules.engine import RuleEngine


def ev(**kwargs):
    base = {
        "event_id": "e",
        "ts": datetime.now(timezone.utc),
        "venue": "SIM",
        "asset_class": "equity",
        "symbol": "SPY",
        "account_id": "acct-x",
        "side": "BUY",
        "event_type": "trade",
        "quantity": 10.0,
        "price": 100.0,
        "order_type": "LIMIT",
        "metadata": {},
    }
    base.update(kwargs)
    return MarketEvent(**base)


def test_cross_asset_spoofing_alert() -> None:
    engine = RuleEngine()
    engine.process(ev(symbol="ES", event_type="trade", metadata={}))
    alerts = engine.process(ev(symbol="SPY", event_type="cancel", metadata={"spoofing_signal": True}))
    assert any(a.pattern == "cross_asset_spoofing" for a in alerts)
