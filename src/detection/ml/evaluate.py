from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score


@dataclass
class EvaluationMetrics:
    precision: float
    recall: float
    f1: float
    auc_roc: float


def evaluate_binary_classifier(y_true: np.ndarray, y_pred: np.ndarray, y_score: np.ndarray) -> EvaluationMetrics:
    return EvaluationMetrics(
        precision=float(precision_score(y_true, y_pred, zero_division=0)),
        recall=float(recall_score(y_true, y_pred, zero_division=0)),
        f1=float(f1_score(y_true, y_pred, zero_division=0)),
        auc_roc=float(roc_auc_score(y_true, y_score)),
    )
