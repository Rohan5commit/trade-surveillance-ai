from __future__ import annotations

import numpy as np


def population_stability_index(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    expected = np.asarray(expected).flatten()
    actual = np.asarray(actual).flatten()
    if expected.size == 0 or actual.size == 0:
        return 0.0

    quantiles = np.linspace(0, 1, bins + 1)
    breaks = np.unique(np.quantile(expected, quantiles))
    if breaks.size < 3:
        return 0.0

    expected_hist, _ = np.histogram(expected, bins=breaks)
    actual_hist, _ = np.histogram(actual, bins=breaks)

    expected_pct = np.clip(expected_hist / max(expected_hist.sum(), 1), 1e-8, 1)
    actual_pct = np.clip(actual_hist / max(actual_hist.sum(), 1), 1e-8, 1)
    psi = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
    return float(psi)


def has_mean_shift(expected: np.ndarray, actual: np.ndarray, std_multiples: float = 3.0) -> bool:
    expected = np.asarray(expected).flatten()
    actual = np.asarray(actual).flatten()
    if expected.size == 0 or actual.size == 0:
        return False
    mu = expected.mean()
    sigma = expected.std() + 1e-9
    return abs(actual.mean() - mu) > std_multiples * sigma
