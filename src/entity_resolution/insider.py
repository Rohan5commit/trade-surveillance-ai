from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InsiderLink:
    trader_account: str
    insider_entity: str
    relation: str
    confidence: float


def detect_insider_links(relationships: list[tuple[str, str, str]]) -> list[InsiderLink]:
    """Input tuples: (account_id, entity_id, relation_type)."""
    links: list[InsiderLink] = []
    for account_id, entity_id, relation in relationships:
        if relation in {"employee", "family", "beneficial_owner"}:
            confidence = 0.9 if relation == "employee" else 0.75
            links.append(InsiderLink(account_id, entity_id, relation, confidence))
    return links
