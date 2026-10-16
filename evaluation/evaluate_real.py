"""Evaluate JobTest on an AUTHORISED, annotated real dataset (local only).

Nothing here has been run on real data yet: the project contains no real,
authorised and labelled CV/offer pairs. See ``evaluation/REAL_DATA_PROTOCOL.md``.

Expected input (never committed — ``data/real/`` is git-ignored):
  data/real/pairs.csv with columns
    pair_id, job_id, cv_text, job_text, label_a, label_b, label_final
  labels in {REJECT, CONSIDER, HIRE}; label_a / label_b are two independent
  recruiter annotations, label_final the adjudicated label.

Protocol implemented:
  1. agreement between annotators (quadratic-weighted kappa) on raw labels;
  2. split by job_id (offers never shared between halves) BEFORE any fitting:
     50 % calibration / 50 % test, seed 42; the split is saved;
  3. scoring with the production models (local inference only);
  4. on the test half: verdicts of the current (synthetic) calibration, and of
     cut points re-fitted on the calibration half only.
Only aggregate metrics are written (evaluation/results/real_eval.json, git-ignored):
no CV text, name or identifier leaves the machine.

Usage: python evaluation/evaluate_real.py [--pairs data/real/pairs.csv]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score
from sklearn.model_selection import GroupShuffleSplit

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / "evaluation"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from calibration_study import CLASSES, bootstrap, fit_cuts, three_class_report, verdicts  # noqa: E402

MIN_TEST_PAIRS = 60


def main(pairs_path: Path) -> dict:
    df = pd.read_csv(pairs_path)
    required = {"pair_id", "job_id", "cv_text", "job_text", "label_a", "label_b", "label_final"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Missing columns: {sorted(missing)}")
    to_int = {c: i for i, c in enumerate(CLASSES)}
    for col in ("label_a", "label_b", "label_final"):
        df[col] = df[col].str.upper().map(to_int)
        if df[col].isna().any():
            raise SystemExit(f"Unknown label values in {col}; expected {CLASSES}.")
    report = {
        "n_pairs": int(len(df)), "n_jobs": int(df["job_id"].nunique()),
        "annotator_agreement_quadratic_kappa": round(float(cohen_kappa_score(
            df["label_a"], df["label_b"], weights="quadratic")), 4),
    }

    splitter = GroupShuffleSplit(n_splits=1, test_size=0.5, random_state=42)
    cal_idx, test_idx = next(splitter.split(df, groups=df["job_id"]))
    df["split"] = "calibration"
    df.loc[df.index[test_idx], "split"] = "test"
    df[["pair_id", "split"]].to_csv(pairs_path.with_name("split_assignment.csv"), index=False)

    from src.models.model_loader import load_production_models
    from src.matching.service import score_pair
    models = load_production_models()
    scored = [score_pair(models, cv, job, "hybrid") for cv, job in zip(df["cv_text"], df["job_text"])]
    df["raw"] = [s["raw_score"] for s in scored]
    df["pct"] = [s["percentage"] for s in scored]
    current_version = scored[0]["calibration_version"] if scored else None

    cal, test = df[df["split"] == "calibration"], df[df["split"] == "test"]
    y_test = test["label_final"].to_numpy()
    current = np.where(test["pct"] >= 75, 2, np.where(test["pct"] >= 55, 1, 0))
    c1, c2 = fit_cuts(cal["raw"].to_numpy(), cal["label_final"].to_numpy())
    refit = verdicts(test["raw"].to_numpy(), c1, c2)

    report.update({
        "split": {"calibration": int(len(cal)), "test": int(len(test))},
        "warning": (f"Test half has fewer than {MIN_TEST_PAIRS} pairs: results are indicative only."
                    if len(test) < MIN_TEST_PAIRS else None),
        "current_calibration": {"version": current_version, **three_class_report(y_test, current),
                                **bootstrap(y_test, current)},
        "refit_on_real_calibration_half": {"cuts": [round(c1, 4), round(c2, 4)],
                                           **three_class_report(y_test, refit), **bootstrap(y_test, refit)},
    })
    out = ROOT / "evaluation" / "results" / "real_eval.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", default=str(ROOT / "data" / "real" / "pairs.csv"))
    args = parser.parse_args()
    path = Path(args.pairs)
    if not path.exists():
        raise SystemExit(f"{path} not found. No real evaluation has been run; see evaluation/REAL_DATA_PROTOCOL.md.")
    print(json.dumps(main(path), indent=2))
