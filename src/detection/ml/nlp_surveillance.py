from __future__ import annotations

from dataclasses import dataclass


RISK_KEYWORDS = {
    "inside info": 0.9,
    "pump": 0.8,
    "dump": 0.8,
    "spoof": 0.85,
    "wash": 0.85,
    "off-book": 0.75,
}


@dataclass
class NlpRisk:
    score: float
    triggers: list[str]


def keyword_risk_score(text: str) -> NlpRisk:
    lower = text.lower()
    triggers = [k for k in RISK_KEYWORDS if k in lower]
    if not triggers:
        return NlpRisk(score=0.0, triggers=[])
    score = min(1.0, sum(RISK_KEYWORDS[t] for t in triggers) / len(triggers))
    return NlpRisk(score=round(score, 4), triggers=triggers)
