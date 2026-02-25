from __future__ import annotations

import argparse
import json

from src.detection.ml.training_pipeline import train_and_register


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrain supervised surveillance model")
    parser.add_argument("--dataset", required=True, help="CSV path with label column")
    parser.add_argument("--model-name", default="svm_market_abuse")
    args = parser.parse_args()

    metrics = train_and_register(args.dataset, model_name=args.model_name)
    print(json.dumps(metrics, indent=2))
