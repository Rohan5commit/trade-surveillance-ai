from __future__ import annotations

from datetime import datetime, timezone
import uuid

from src.common.schemas import MarketEvent


FIX_SIDE_MAP = {"1": "BUY", "2": "SELL"}
FIX_EVENT_MAP = {
    "D": "new_order",  # NewOrderSingle
    "F": "cancel",  # OrderCancelRequest
    "8": "fill",  # ExecutionReport (can also be trade)
}


def parse_fix_message(raw: str, venue: str = "FIX") -> MarketEvent | None:
    """Parse a FIX message into the canonical MarketEvent schema.

    Supports common tags required for surveillance MVP.
    """
    if not raw:
        return None

    delim = "\x01" if "\x01" in raw else "|"
    tags: dict[str, str] = {}
    for part in raw.strip().split(delim):
        if not part or "=" not in part:
            continue
        k, v = part.split("=", 1)
        tags[k] = v

    msg_type = tags.get("35")
    if msg_type not in FIX_EVENT_MAP:
        return None

    event_type = FIX_EVENT_MAP[msg_type]
    if msg_type == "8" and tags.get("150") == "F":  # Trade
        event_type = "trade"

    ts = _parse_fix_ts(tags.get("60"))
    symbol = tags.get("55", "UNKNOWN")
    account_id = tags.get("1", "unknown-account")
    side = FIX_SIDE_MAP.get(tags.get("54", "1"), "BUY")

    quantity = _to_float(tags.get("38"), default=1.0)
    price = _to_float(tags.get("44"), default=1.0)

    return MarketEvent(
        event_id=str(uuid.uuid4()),
        ts=ts,
        venue=tags.get("207", venue),
        asset_class=_guess_asset_class(symbol),
        symbol=symbol,
        account_id=account_id,
        side=side,
        event_type=event_type,
        order_id=tags.get("37") or tags.get("11"),
        trade_id=tags.get("17"),
        counterparty_account_id=tags.get("375"),
        quantity=max(quantity, 1e-9),
        price=max(price, 1e-9),
        order_type=tags.get("40", "LIMIT"),
        metadata={"fix_msg_type": msg_type},
    )


def _parse_fix_ts(raw: str | None) -> datetime:
    if not raw:
        return datetime.now(timezone.utc)
    for fmt in ("%Y%m%d-%H:%M:%S.%f", "%Y%m%d-%H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def _to_float(raw: str | None, default: float) -> float:
    try:
        return float(raw) if raw is not None else default
    except (TypeError, ValueError):
        return default


def _guess_asset_class(symbol: str) -> str:
    upper = symbol.upper()
    if "USDT" in upper or "BTC" in upper or "ETH" in upper:
        return "crypto"
    if upper.endswith("C") or upper.endswith("P"):
        return "option"
    return "equity"
