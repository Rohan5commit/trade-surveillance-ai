from src.detection.hybrid.scorer import combine_scores


def test_hybrid_scoring_band() -> None:
    score = combine_scores(0.9, 0.8, 0.6)
    assert score.final_score > 0.7
    assert score.severity in {"high", "critical"}
