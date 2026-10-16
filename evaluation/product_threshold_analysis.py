"""Read-only diagnostic of the recorded benchmark at the product thresholds.

Reads ``evaluation/results/evaluation_results.json`` (produced by
``EvaluationSuite.run_full_evaluation``) and writes
``evaluation/results/product_threshold_analysis.json``. Nothing here selects a
weight or a threshold: the product bounds (55 % / 75 %) are the
``DecisionEngine`` defaults and the experimental threshold is the one already
chosen on validation. The script only re-reads the stored test scores to

* check that the stored hybrid scores equal 0.2*tfidf + 0.4*embedding + 0.4*skill,
* recompute the metrics of the hybrid score at 0.2636, 0.55 and 0.75,
* describe the score distribution per label and per component,
* run a McNemar test between TF-IDF and the hybrid at their own thresholds.

Usage: python evaluation/product_threshold_analysis.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import chi2
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.decisioning.decision_engine import DEFAULT_POTENTIAL_FIT, DEFAULT_STRONG_FIT  # noqa: E402

RESULTS = ROOT / "evaluation" / "results" / "evaluation_results.json"
OUTPUT = ROOT / "evaluation" / "results" / "product_threshold_analysis.json"


def _describe(values: np.ndarray) -> dict:
    return {
        "min": round(float(values.min()), 4),
        "p10": round(float(np.percentile(values, 10)), 4),
        "median": round(float(np.median(values)), 4),
        "p90": round(float(np.percentile(values, 90)), 4),
        "max": round(float(values.max()), 4),
        "share_zero": round(float(np.mean(values == 0.0)), 4),
    }


def _reading(y_true: np.ndarray, scores: np.ndarray, threshold: float) -> dict:
    y_pred = (scores >= threshold).astype(int)
    return {
        "threshold": threshold,
        "predicted_positive": int(y_pred.sum()),
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4) if y_pred.sum() else None,
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
    }


def _mcnemar(y_true: np.ndarray, pred_a: np.ndarray, pred_b: np.ndarray) -> dict:
    a_ok, b_ok = pred_a == y_true, pred_b == y_true
    b01 = int(np.sum(a_ok & ~b_ok))
    b10 = int(np.sum(~a_ok & b_ok))
    stat = (abs(b01 - b10) - 1) ** 2 / max(1, b01 + b10)
    return {"a_right_b_wrong": b01, "a_wrong_b_right": b10, "statistic": round(float(stat), 4),
            "p_value": float(chi2.sf(stat, 1))}


def main() -> dict:
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    metrics = data["metrics"]
    weights = data["analysis"]["fixed_fusion_weights"]

    comp = {name: np.asarray(metrics[name]["scores"], dtype=float) for name in ("tfidf", "embedding", "skill")}
    hybrid = np.asarray(metrics["hybrid"]["scores"], dtype=float)

    preds = {name: np.asarray(metrics[name]["predictions"], dtype=int) for name in metrics}

    # Ground truth is not serialised with the scores. The split is deterministic
    # (seed 42), so it is rebuilt here and checked against every stored
    # confusion matrix before use. Re-running the split loads no model.
    import pandas as pd
    from src.evaluation.evaluator import EvaluationSuite

    df = pd.read_csv(ROOT / "data" / "datasets" / "cv_job_dataset.csv")
    test = EvaluationSuite.stratified_split(df).test
    y_true = test["label"].astype(int).to_numpy()
    if len(y_true) != len(hybrid):
        raise SystemExit("Test split size does not match the stored scores.")
    for name, m in metrics.items():
        cm = np.asarray(m["confusion_matrix"])
        p = preds[name]
        rebuilt = np.array([[np.sum((y_true == 0) & (p == 0)), np.sum((y_true == 0) & (p == 1))],
                            [np.sum((y_true == 1) & (p == 0)), np.sum((y_true == 1) & (p == 1))]])
        if not np.array_equal(cm, rebuilt):
            raise SystemExit(f"Reconstructed labels disagree with stored confusion matrix for {name}.")

    recomposed = weights["tfidf"] * comp["tfidf"] + weights["embedding"] * comp["embedding"] + weights["skill"] * comp["skill"]
    recomposed = np.clip(recomposed, 0.0, 1.0)
    max_abs_gap = float(np.max(np.abs(recomposed - hybrid)))

    experimental = float(metrics["hybrid"]["operating_threshold"])
    readings = {
        "experimental_validation_threshold": _reading(y_true, hybrid, experimental),
        "product_consider": _reading(y_true, hybrid, DEFAULT_POTENTIAL_FIT / 100.0),
        "product_hire": _reading(y_true, hybrid, DEFAULT_STRONG_FIT / 100.0),
    }
    # Verdicts as the interface would show them (REJECT / CONSIDER / HIRE).
    pct = hybrid * 100.0
    verdicts = {
        "HIRE": int(np.sum(pct >= DEFAULT_STRONG_FIT)),
        "CONSIDER": int(np.sum((pct >= DEFAULT_POTENTIAL_FIT) & (pct < DEFAULT_STRONG_FIT))),
        "REJECT": int(np.sum(pct < DEFAULT_POTENTIAL_FIT)),
    }

    distribution = {"hybrid": {}, "components": {}}
    for label in (0, 1):
        mask = y_true == label
        distribution["hybrid"][f"label_{label}"] = {"count": int(mask.sum()), **_describe(hybrid[mask])}
        for name, values in comp.items():
            distribution["components"].setdefault(name, {})[f"label_{label}"] = _describe(values[mask])
    # Ceiling actually reachable on this corpus if each component were at its
    # observed 90th percentile among positives.
    pos = y_true == 1
    p90_positive_combo = sum(weights[n] * float(np.percentile(comp[n][pos], 90)) for n in comp)

    payload = {
        "source": str(RESULTS.relative_to(ROOT)).replace("\\", "/"),
        "test_size": int(len(y_true)),
        "positives": int(y_true.sum()),
        "negatives": int((1 - y_true).sum()),
        "weights": weights,
        "formula_check": {"max_abs_gap_stored_vs_recomposed": round(max_abs_gap, 6),
                          "consistent": max_abs_gap <= 1e-3},
        "readings": readings,
        "interface_verdicts_on_test": verdicts,
        "distribution": distribution,
        "weighted_p90_of_positive_components": round(p90_positive_combo, 4),
        "mcnemar_tfidf_vs_hybrid": _mcnemar(y_true, preds["tfidf"], preds["hybrid"]),
        "bootstrap_f1_ci": {n: data["analysis"]["bootstrap_ci"][n]["f1"] for n in ("tfidf", "hybrid")},
        "note": "Descriptive re-reading of stored test scores; no weight or threshold is selected here.",
    }
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
