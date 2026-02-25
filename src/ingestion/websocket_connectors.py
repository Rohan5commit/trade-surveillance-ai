from __future__ import annotations

from datetime import datetime, timezone
import json
import uuid

from websocket import create_connection

from src.common.schemas import MarketEvent


class BinanceTradeConnector:
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol.lower()
        self.url = f"wss://stream.binance.com:9443/ws/{self.symbol}@trade"

    def stream_events(self):
        ws = create_connection(self.url)
        try:
            while True:
                payload = json.loads(ws.recv())
                qty = float(payload.get("q", 0.0) or 0.0)
                price = float(payload.get("p", 0.0) or 0.0)
                if qty <= 0 or price <= 0:
                    continue

                yield MarketEvent(
                    event_id=str(payload.get("t", uuid.uuid4())),
                    ts=datetime.fromtimestamp(payload.get("T", 0) / 1000, tz=timezone.utc),
                    venue="BINANCE",
                    asset_class="crypto",
                    symbol=payload.get("s", self.symbol.upper()),
                    account_id="exchange-public-feed",
                    side="SELL" if payload.get("m") else "BUY",
                    event_type="trade",
                    trade_id=str(payload.get("a", "")) or None,
                    quantity=qty,
                    price=price,
                    order_type="MARKET",
                    metadata={"source": "binance_ws"},
                )
        finally:
            ws.close()


class CoinbaseTradeConnector:
    def __init__(self, product_id: str) -> None:
        self.product_id = product_id
        self.url = "wss://ws-feed.exchange.coinbase.com"

    def stream_events(self):
        ws = create_connection(self.url)
        subscribe = {
            "type": "subscribe",
            "product_ids": [self.product_id],
            "channels": ["matches"],
        }
        ws.send(json.dumps(subscribe))
        try:
            while True:
                payload = json.loads(ws.recv())
                if payload.get("type") != "match":
                    continue
                qty = float(payload.get("size", 0.0) or 0.0)
                price = float(payload.get("price", 0.0) or 0.0)
                if qty <= 0 or price <= 0:
                    continue

                yield MarketEvent(
                    event_id=str(payload.get("trade_id", uuid.uuid4())),
                    ts=datetime.fromisoformat(payload["time"].replace("Z", "+00:00")),
                    venue="COINBASE",
                    asset_class="crypto",
                    symbol=payload.get("product_id", self.product_id),
                    account_id="exchange-public-feed",
                    side="SELL" if payload.get("side") == "sell" else "BUY",
                    event_type="trade",
                    trade_id=str(payload.get("trade_id", "")) or None,
                    quantity=qty,
                    price=price,
                    order_type="MARKET",
                    metadata={"source": "coinbase_ws"},
                )
        finally:
            ws.close()
