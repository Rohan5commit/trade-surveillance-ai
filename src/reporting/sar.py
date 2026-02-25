from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class SarPayload:
    case_id: int
    subject: str
    activity_type: str
    amount_usd: float
    start_date: datetime
    end_date: datetime
    narrative: str


def render_sar_markdown(payload: SarPayload) -> str:
    return f"""# Suspicious Activity Report (SAR)

- Case ID: {payload.case_id}
- Subject: {payload.subject}
- Activity Type: {payload.activity_type}
- Amount (USD): {payload.amount_usd:,.2f}
- Activity Window: {payload.start_date.isoformat()} to {payload.end_date.isoformat()}

## Narrative
{payload.narrative}
"""
