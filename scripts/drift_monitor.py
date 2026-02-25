from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd

from src.detection.ml.drift import has_mean_shift, population_stability_index


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check feature drift between baseline and current windows")
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--current", required=True)
    parser.add_argument("--psi-threshold", type=float, default=0.25)
    args = parser.parse_args()

    base = pd.read_csv(args.baseline)
    cur = pd.read_csv(args.current)

    common = [c for c in base.columns if c in cur.columns]
    if not common:
        raise ValueError("No overlapping feature columns")

    report: dict[str, dict[str, float | bool]] = {}
    for col in common:
        b = np.asarray(base[col].dropna().to_numpy(dtype=float))
        c = np.asarray(cur[col].dropna().to_numpy(dtype=float))
        psi = population_stability_index(b, c)
        report[col] = {
            "psi": round(psi, 6),
            "psi_alert": psi >= args.psi_threshold,
            "mean_shift": has_mean_shift(b, c),
        }

    print(json.dumps(report, indent=2))
