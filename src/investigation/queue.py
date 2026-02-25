from __future__ import annotations

from dataclasses import dataclass

from src.common.schemas import Alert


@dataclass
class QueuePriority:
    alert_id: str
    score: float


def prioritize_alert(alert: Alert, regulatory_deadline_days: int, account_risk_tier: int, age_minutes: int) -> QueuePriority:
    # Higher score => earlier investigation.
    deadline_factor = max(0.0, 1.0 - regulatory_deadline_days / 30)
    risk_factor = min(max(account_risk_tier / 5, 0.0), 1.0)
    age_factor = min(age_minutes / 60, 1.0)
    score = 0.5 * alert.score + 0.2 * deadline_factor + 0.2 * risk_factor + 0.1 * age_factor
    return QueuePriority(alert_id=alert.alert_id, score=round(score, 4))
