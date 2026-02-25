from __future__ import annotations

from datetime import datetime
from pathlib import Path

from imblearn.over_sampling import BorderlineSMOTE
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from src.detection.ml.evaluate import evaluate_binary_classifier
from src.detection.ml.model_registry import LocalModelRegistry, ModelVersion
from src.detection.ml.supervised import train_rbf_svm


def load_labeled_dataset(path: str) -> tuple[np.ndarray, np.ndarray]:
    df = pd.read_csv(path)
    if "label" not in df.columns:
        raise ValueError("Dataset must include 'label' column")
    y = df["label"].astype(int).to_numpy()
    X = df.drop(columns=["label"]).to_numpy(dtype=float)
    return X, y


def train_and_register(dataset_path: str, model_name: str = "svm_market_abuse") -> dict[str, float]:
    X, y = load_labeled_dataset(dataset_path)
    X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, test_size=0.2, random_state=42)

    smote = BorderlineSMOTE(random_state=42, k_neighbors=3)
    X_resampled, y_resampled = smote.fit_resample(X_train, y_train)

    model, _ = train_rbf_svm(X_resampled, y_resampled)

    proba = model.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)
    metrics = evaluate_binary_classifier(y_test, pred, proba)

    artifact_dir = Path("models")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / f"{model_name}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.joblib"

    # Avoid hard dependency on joblib in runtime path if missing.
    import joblib

    joblib.dump(model, artifact_path)

    registry = LocalModelRegistry()
    registry.register(
        ModelVersion(
            name=model_name,
            version=datetime.utcnow().strftime("%Y%m%d%H%M%S"),
            metrics={
                "precision": metrics.precision,
                "recall": metrics.recall,
                "f1": metrics.f1,
                "auc_roc": metrics.auc_roc,
            },
            artifact_uri=str(artifact_path),
        )
    )
    return {
        "precision": metrics.precision,
        "recall": metrics.recall,
        "f1": metrics.f1,
        "auc_roc": metrics.auc_roc,
    }
