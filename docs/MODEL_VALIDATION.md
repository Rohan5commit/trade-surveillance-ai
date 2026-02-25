# Model Validation

## Validation Strategy
- Hold-out validation via `train_test_split` in `src/detection/ml/training_pipeline.py`.
- Class imbalance handled with Borderline SMOTE.
- Metrics captured: precision, recall, F1, AUC-ROC.
- Registry records version + artifact path + metrics.

## Drift Monitoring
- PSI and mean-shift checks in `src/detection/ml/drift.py`.
- Scheduled run in `.github/workflows/drift-monitor.yml`.

## Retraining
- Scheduled run in `.github/workflows/retrain.yml`.
- Manual command:
  - `python scripts/retrain.py --dataset data/labeled_sample.csv --model-name svm_market_abuse`

## Explainability
- Deterministic evidence in all rule-based alerts.
- SHAP/LIME path available via optional dependencies.
