from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class CommunicationEvent:
    source: str  # email/chat/voice
    ts: datetime
    participant_ids: list[str]
    text: str
    metadata: dict


def link_communications_to_account(communications: list[CommunicationEvent], account_participants: set[str]) -> list[CommunicationEvent]:
    return [c for c in communications if any(p in account_participants for p in c.participant_ids)]
