from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.svm import SVC

try:
    import xgboost as xgb
except Exception:  # pragma: no cover
    xgb = None


@dataclass
class SupervisedMetrics:
    auc_roc: float
    auc_pr: float


def train_rbf_svm(X: np.ndarray, y: np.ndarray) -> tuple[SVC, SupervisedMetrics]:
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    model = SVC(kernel="rbf", probability=True)
    grid = GridSearchCV(
        model,
        param_grid={"C": [0.1, 1.0, 10.0], "gamma": ["scale", "auto"]},
        scoring="average_precision",
        cv=3,
        n_jobs=-1,
    )
    grid.fit(X_train, y_train)

    proba = grid.best_estimator_.predict_proba(X_test)[:, 1]
    metrics = SupervisedMetrics(
        auc_roc=float(roc_auc_score(y_test, proba)),
        auc_pr=float(average_precision_score(y_test, proba)),
    )
    return grid.best_estimator_, metrics


def train_xgboost(X: np.ndarray, y: np.ndarray, scale_pos_weight: float = 99.0) -> tuple[Any, SupervisedMetrics]:
    if xgb is None:
        raise RuntimeError("xgboost is not installed. Install requirements-optional.txt")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        eval_metric="logloss",
    )
    model.fit(X_train, y_train)

    proba = model.predict_proba(X_test)[:, 1]
    metrics = SupervisedMetrics(
        auc_roc=float(roc_auc_score(y_test, proba)),
        auc_pr=float(average_precision_score(y_test, proba)),
    )
    return model, metrics
