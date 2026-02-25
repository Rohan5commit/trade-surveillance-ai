from __future__ import annotations

from dataclasses import dataclass

from src.common.schemas import MarketEvent


@dataclass
class SecurityMasterRecord:
    canonical_symbol: str
    isin: str | None
    cusip: str | None
    ric: str | None
    tick_size: float


SECURITY_MASTER: dict[str, SecurityMasterRecord] = {
    "AAPL": SecurityMasterRecord("AAPL", "US0378331005", "037833100", "AAPL.O", 0.01),
    "MSFT": SecurityMasterRecord("MSFT", "US5949181045", "594918104", "MSFT.O", 0.01),
}


def enrich_event(event: MarketEvent) -> MarketEvent:
    sm = SECURITY_MASTER.get(event.symbol)
    if not sm:
        return event

    metadata = dict(event.metadata)
    metadata.update(
        {
            "isin": sm.isin or "",
            "cusip": sm.cusip or "",
            "ric": sm.ric or "",
            "tick_size": sm.tick_size,
        }
    )
    return event.model_copy(update={"symbol": sm.canonical_symbol, "metadata": metadata})
