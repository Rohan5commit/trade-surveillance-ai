import numpy as np

from src.detection.ml.drift import population_stability_index


def test_psi_non_negative() -> None:
    expected = np.array([1, 2, 3, 4, 5, 6], dtype=float)
    actual = np.array([1, 2, 3, 3, 4, 5], dtype=float)
    psi = population_stability_index(expected, actual)
    assert psi >= 0
