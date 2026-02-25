from __future__ import annotations

import networkx as nx

from src.common.schemas import MarketEvent


class WashTradeGraphDetector:
    def __init__(self) -> None:
        self.graph = nx.DiGraph()

    def ingest_trade(self, event: MarketEvent) -> None:
        if event.event_type != "trade" or not event.counterparty_account_id:
            return
        buyer = event.account_id if event.side == "BUY" else event.counterparty_account_id
        seller = event.counterparty_account_id if event.side == "BUY" else event.account_id
        weight = self.graph.get_edge_data(buyer, seller, {}).get("volume", 0.0)
        self.graph.add_edge(buyer, seller, volume=weight + event.quantity)

    def suspicious_cycles(self, min_cycle_len: int = 2, max_cycle_len: int = 6) -> list[list[str]]:
        cycles: list[list[str]] = []
        for cycle in nx.simple_cycles(self.graph):
            if min_cycle_len <= len(cycle) <= max_cycle_len:
                cycles.append(cycle)
        return cycles
