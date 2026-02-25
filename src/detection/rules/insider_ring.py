from __future__ import annotations

from collections import defaultdict

import numpy as np

from src.common.schemas import MarketEvent


def co_trading_correlation(events: list[MarketEvent], target_symbol: str) -> dict[tuple[str, str], float]:
    by_account: dict[str, list[float]] = defaultdict(list)
    for e in events:
        if e.symbol != target_symbol or e.event_type not in {"trade", "fill"}:
            continue
        signed = e.quantity if e.side == "BUY" else -e.quantity
        by_account[e.account_id].append(signed)

    accounts = list(by_account.keys())
    out: dict[tuple[str, str], float] = {}
    for i in range(len(accounts)):
        for j in range(i + 1, len(accounts)):
            a, b = accounts[i], accounts[j]
            va, vb = by_account[a], by_account[b]
            n = min(len(va), len(vb))
            if n < 3:
                continue
            ca = np.array(va[:n], dtype=float)
            cb = np.array(vb[:n], dtype=float)
            if ca.std() == 0 or cb.std() == 0:
                continue
            corr = float(np.corrcoef(ca, cb)[0, 1])
            out[(a, b)] = corr
    return out


def suspicious_pairs(events: list[MarketEvent], target_symbol: str, threshold: float = 0.7) -> list[tuple[str, str, float]]:
    corr = co_trading_correlation(events, target_symbol)
    return [(a, b, c) for (a, b), c in corr.items() if c >= threshold]
