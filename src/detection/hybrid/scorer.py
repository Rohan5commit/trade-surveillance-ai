from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HybridScore:
    final_score: float
    severity: str


def combine_scores(rule_based_score: float, ml_anomaly_score: float, historical_account_risk: float) -> HybridScore:
    score = 0.4 * rule_based_score + 0.4 * ml_anomaly_score + 0.2 * historical_account_risk
    if score > 0.9:
        severity = "critical"
    elif score > 0.7:
        severity = "high"
    elif score > 0.5:
        severity = "medium"
    else:
        severity = "low"
    return HybridScore(final_score=round(score, 4), severity=severity)
