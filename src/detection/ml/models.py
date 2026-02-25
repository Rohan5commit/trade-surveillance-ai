from __future__ import annotations

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM


class UnsupervisedEnsemble:
    def __init__(self, contamination: float = 0.01) -> None:
        self.scaler = StandardScaler()
        self.isolation_forest = IsolationForest(
            n_estimators=200,
            contamination=contamination,
            random_state=42,
        )
        self.one_class_svm = OneClassSVM(kernel="rbf", gamma="scale", nu=contamination)
        self.dbscan = DBSCAN(eps=0.9, min_samples=10)
        self._fitted = False

    @property
    def fitted(self) -> bool:
        return self._fitted

    def fit(self, X: np.ndarray) -> None:
        Xs = self.scaler.fit_transform(X)
        self.isolation_forest.fit(Xs)
        self.one_class_svm.fit(Xs)
        self.dbscan.fit(Xs)
        self._fitted = True

    def score(self, X: np.ndarray) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("Model ensemble is not fitted")
        Xs = self.scaler.transform(X)

        iso_score = -self.isolation_forest.score_samples(Xs)
        svm_pred = self.one_class_svm.predict(Xs)
        svm_score = np.where(svm_pred == -1, 1.0, 0.0)
        dbscan_pred = self.dbscan.fit_predict(Xs)
        dbscan_score = np.where(dbscan_pred == -1, 1.0, 0.0)

        # Weighted blend, normalized to [0,1].
        raw = 0.6 * (iso_score / (iso_score.max() + 1e-9)) + 0.25 * svm_score + 0.15 * dbscan_score
        return np.clip(raw, 0.0, 1.0)
