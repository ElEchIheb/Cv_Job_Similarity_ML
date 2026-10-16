"""Calibration study: method selection (train/validation) then ONE test read.

Inputs: component caches written by ``evaluation/compute_components.py``.

Stage ``select`` (no test data is read):
  * candidate scores: documented hybrid 0.2/0.4/0.4, each single component, and
    a learned fusion whose weights are fitted on a TRAINING sample only;
  * for every candidate, two cut points on the raw score are fitted on the
    validation split by maximising the 3-class macro-F1 of the verdict
    (REJECT / CONSIDER / HIRE vs the generator's unrelated / transferable /
    strong classes). Selection uses 5-fold cross-validated macro-F1 inside the
    validation split, so the cut points are always scored on unseen pairs;
  * pre-registered rule: keep the best cross-validated macro-F1 among the
    candidates whose verdict downgrade rate under alias rewriting (validation
    alias set) does not exceed the documented hybrid's by more than 5 points.

Stage ``final`` (reads the isolated test split once, writes a marker):
  * fits the cut points of every method on the full validation split, writes
    ``models/checkpoints/score_calibration.json`` and reports test metrics for
    the product BEFORE (raw x 100 at 55/75, with the old 0-1/0-100 quirk) and
    AFTER (calibrated scale at 55/75), plus the experimental-threshold reading.

Stage ``write`` (validation only) re-writes the calibration file for a given
candidate, recording why it differs from the rule winner (product decision).

Usage:
  python evaluation/calibration_study.py select
  python evaluation/calibration_study.py final
  python evaluation/calibration_study.py write --hybrid-candidate hybrid_documented --note "..."
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (average_precision_score, cohen_kappa_score, confusion_matrix,
                             f1_score, precision_recall_fscore_support, roc_auc_score)
from sklearn.model_selection import StratifiedKFold

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CACHE = ROOT / "evaluation" / "cache"
RESULTS = ROOT / "evaluation" / "results"
SELECTION_FILE = RESULTS / "calibration_selection.json"
FINAL_FILE = RESULTS / "calibration_study.json"
TEST_MARKER = RESULTS / ".calibration_test_read"
CALIBRATION_OUT = ROOT / "models" / "checkpoints" / "score_calibration.json"
DATASET = ROOT / "data" / "datasets" / "cv_job_dataset.csv"

COMPONENTS = ("tfidf", "embedding", "skill")
DOCUMENTED = {"tfidf": 0.2, "embedding": 0.4, "skill": 0.4}
SINGLE = {name: {n: float(n == name) for n in COMPONENTS} for name in COMPONENTS}
CONSIDER_DISPLAY, HIRE_DISPLAY = 55.0, 75.0
ROBUSTNESS_MARGIN = 0.05
CLASSES = ["REJECT", "CONSIDER", "HIRE"]


# ── data ─────────────────────────────────────────────────────────────────────
def load(tag: str) -> pd.DataFrame:
    frame = pd.read_csv(CACHE / f"components_{tag}.csv")
    frame["y3"] = frame["score_raw"].map({0.0: 0, 0.5: 1, 1.0: 2}).astype(int)
    return frame


def raw_score(frame: pd.DataFrame, weights: dict) -> np.ndarray:
    return sum(weights[n] * frame[n].to_numpy(dtype=float) for n in COMPONENTS)


# ── learned fusion (training sample only) ────────────────────────────────────
def fit_fusion_weights(train: pd.DataFrame, step: float = 0.05) -> dict:
    """Non-negative weights on the simplex maximising the mean of the two
    ordinal AUCs (>= transferable vs unrelated, strong vs the rest)."""
    y_bin = (train["y3"] >= 1).astype(int).to_numpy()
    y_strong = (train["y3"] == 2).astype(int).to_numpy()
    grid = np.round(np.arange(0.0, 1.0 + 1e-9, step), 4)
    best, best_value = None, -1.0
    for wt, we in itertools.product(grid, grid):
        ws = round(1.0 - wt - we, 4)
        if ws < -1e-9:
            continue
        weights = {"tfidf": float(wt), "embedding": float(we), "skill": float(max(ws, 0.0))}
        s = raw_score(train, weights)
        value = 0.5 * (roc_auc_score(y_bin, s) + roc_auc_score(y_strong, s))
        if value > best_value + 1e-12:
            best, best_value = weights, value
    return {"weights": best, "train_mean_auc": round(best_value, 4)}


# ── cut points ───────────────────────────────────────────────────────────────
def verdicts(raw: np.ndarray, c1: float, c2: float) -> np.ndarray:
    return np.where(raw >= c2, 2, np.where(raw >= c1, 1, 0))


def macro_f1(y3: np.ndarray, pred: np.ndarray) -> float:
    """3-class macro-F1 (same definition as sklearn, labels 0/1/2, 0 if empty)."""
    scores = []
    for k in (0, 1, 2):
        tp = np.sum((pred == k) & (y3 == k))
        denom = 2 * tp + np.sum((pred == k) & (y3 != k)) + np.sum((pred != k) & (y3 == k))
        scores.append(2 * tp / denom if denom else 0.0)
    return float(np.mean(scores))


def fit_cuts(raw: np.ndarray, y3: np.ndarray, n_grid: int = 200) -> tuple[float, float]:
    grid = np.unique(np.quantile(raw, np.linspace(0.01, 0.99, n_grid)))
    best, best_value = (float(grid[0]), float(grid[-1])), -1.0
    for i, c1 in enumerate(grid):
        for c2 in grid[i + 1:]:
            value = macro_f1(y3, verdicts(raw, c1, c2))
            if value > best_value + 1e-12:
                best, best_value = (float(c1), float(c2)), value
    return best


def cv_macro_f1(raw: np.ndarray, y3: np.ndarray, folds: int = 5) -> float:
    splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=42)
    predictions = np.zeros_like(y3)
    for fit_idx, eval_idx in splitter.split(raw.reshape(-1, 1), y3):
        c1, c2 = fit_cuts(raw[fit_idx], y3[fit_idx])
        predictions[eval_idx] = verdicts(raw[eval_idx], c1, c2)
    return float(f1_score(y3, predictions, average="macro"))


def display(raw: np.ndarray, c1: float, c2: float, ceiling: float) -> np.ndarray:
    xs, ys = [0.0, c1, c2, ceiling], [0.0, CONSIDER_DISPLAY, HIRE_DISPLAY, 100.0]
    return np.round(np.interp(np.clip(raw, 0.0, None), xs, ys, right=100.0), 1)


def downgrade_rate(base: pd.DataFrame, alias: pd.DataFrame, weights: dict, cuts) -> dict:
    merged = alias.merge(base[["id"] + list(COMPONENTS)], on="id", suffixes=("", "_orig"))
    orig = merged[[f"{n}_orig" for n in COMPONENTS]].copy()
    orig.columns = list(COMPONENTS)
    v_orig = verdicts(raw_score(orig, weights), *cuts)
    v_alias = verdicts(raw_score(merged, weights), *cuts)
    return {
        "n": int(len(merged)),
        "downgrade_rate": round(float(np.mean(v_alias < v_orig)), 4),
        "upgrade_rate": round(float(np.mean(v_alias > v_orig)), 4),
    }


# ── metrics ──────────────────────────────────────────────────────────────────
def three_class_report(y3: np.ndarray, pred: np.ndarray) -> dict:
    p, r, f, s = precision_recall_fscore_support(y3, pred, labels=[0, 1, 2], zero_division=0)
    return {
        "confusion_matrix_rows_true_cols_pred": confusion_matrix(y3, pred, labels=[0, 1, 2]).tolist(),
        "labels": CLASSES,
        "macro_f1": round(float(np.mean(f)), 4),
        "per_class": {c: {"precision": round(float(p[i]), 4), "recall": round(float(r[i]), 4),
                          "f1": round(float(f[i]), 4), "support": int(s[i])} for i, c in enumerate(CLASSES)},
        "quadratic_kappa": round(float(cohen_kappa_score(y3, pred, weights="quadratic")), 4),
        "verdict_counts": {c: int(np.sum(pred == i)) for i, c in enumerate(CLASSES)},
    }


def binary_report(y_bin: np.ndarray, positive_pred: np.ndarray) -> dict:
    tp = int(np.sum((positive_pred == 1) & (y_bin == 1)))
    fp = int(np.sum((positive_pred == 1) & (y_bin == 0)))
    fn = int(np.sum((positive_pred == 0) & (y_bin == 1)))
    tn = int(np.sum((positive_pred == 0) & (y_bin == 0)))
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if precision and recall else 0.0
    return {"confusion_matrix_rows_true_cols_pred": [[tn, fp], [fn, tp]],
            "accuracy": round((tp + tn) / len(y_bin), 4),
            "precision": round(precision, 4) if precision is not None else None,
            "recall": round(recall, 4), "f1": round(f1, 4), "predicted_positive": tp + fp}


def bootstrap(y3: np.ndarray, pred: np.ndarray, iterations: int = 1000) -> dict:
    rng = np.random.default_rng(42)
    macro, binary = [], []
    y_bin = (y3 >= 1).astype(int)
    for _ in range(iterations):
        idx = rng.integers(0, len(y3), len(y3))
        macro.append(f1_score(y3[idx], pred[idx], average="macro", labels=[0, 1, 2], zero_division=0))
        binary.append(f1_score(y_bin[idx], (pred[idx] >= 1).astype(int), zero_division=0))
    q = lambda v: [round(float(np.percentile(v, 2.5)), 4), round(float(np.percentile(v, 97.5)), 4)]  # noqa: E731
    return {"macro_f1_95ci": q(macro), "binary_f1_95ci": q(binary)}


def full_report(frame: pd.DataFrame, raw: np.ndarray, pred: np.ndarray) -> dict:
    y3 = frame["y3"].to_numpy()
    y_bin = (y3 >= 1).astype(int)
    report = {
        "three_class": three_class_report(y3, pred),
        "binary_consider_or_better": binary_report(y_bin, (pred >= 1).astype(int)),
        "binary_hire_vs_strong": binary_report((y3 == 2).astype(int), (pred == 2).astype(int)),
        "ranking": {"roc_auc": round(float(roc_auc_score(y_bin, raw)), 4),
                    "pr_auc": round(float(average_precision_score(y_bin, raw)), 4)},
        "bootstrap": bootstrap(y3, pred),
        "subgroups": {},
    }
    for column in ("language", "difficulty", "domain"):
        rows = {}
        for value, idx in frame.groupby(column).groups.items():
            idx = np.asarray(list(idx))
            sub_y, sub_p = y3[idx], pred[idx]
            rows[str(value)] = {
                "n": int(len(idx)),
                "class_counts": {c: int(np.sum(sub_y == i)) for i, c in enumerate(CLASSES)},
                # accuracy is the meaningful figure when a subgroup holds a single class
                "accuracy": round(float(np.mean(sub_y == sub_p)), 4),
                "macro_f1": round(float(f1_score(sub_y, sub_p, average="macro", labels=[0, 1, 2], zero_division=0)), 4),
                "binary_f1": round(float(f1_score((sub_y >= 1).astype(int), (sub_p >= 1).astype(int), zero_division=0)), 4),
                "verdict_counts": {c: int(np.sum(sub_p == i)) for i, c in enumerate(CLASSES)},
            }
        report["subgroups"][column] = rows
    return report


def legacy_product_verdicts(raw: np.ndarray) -> np.ndarray:
    """Pre-fix behaviour: pct = raw*100 rounded, then the engine re-scaled any
    pct in [0, 1] by 100 before applying 55/75."""
    pct = np.round(raw * 100.0, 1)
    pct = np.where((pct >= 0) & (pct <= 1.0), pct * 100.0, pct)
    return np.where(pct >= 75, 2, np.where(pct >= 55, 1, 0))


def class_balance(frame: pd.DataFrame) -> dict:
    counts = frame["y3"].value_counts().sort_index()
    n = int(len(frame))
    return {"n": n, **{CLASSES[i]: {"count": int(counts.get(i, 0)), "share": round(float(counts.get(i, 0)) / n, 4)}
                       for i in range(3)}}


# ── stages ───────────────────────────────────────────────────────────────────
def candidates(train: pd.DataFrame) -> tuple[dict, dict]:
    fusion = fit_fusion_weights(train)
    cands = {"hybrid_documented": DOCUMENTED, "fusion_learned": fusion["weights"], **SINGLE}
    return cands, fusion


def stage_select() -> dict:
    train, val = load("train_sub"), load("validation")
    val_alias = load("validation_alias")
    cands, fusion = candidates(train)
    y3 = val["y3"].to_numpy()
    table = {}
    for name, weights in cands.items():
        raw = raw_score(val, weights)
        cuts = fit_cuts(raw, y3)
        table[name] = {
            "weights": weights,
            "cv_macro_f1": round(cv_macro_f1(raw, y3), 4),
            "in_sample_macro_f1": round(float(f1_score(y3, verdicts(raw, *cuts), average="macro")), 4),
            "validation_auc": round(float(roc_auc_score((y3 >= 1).astype(int), raw)), 4),
            "cuts": [round(cuts[0], 4), round(cuts[1], 4)],
            "alias_robustness": downgrade_rate(val, val_alias, weights, cuts),
        }
    reference = table["hybrid_documented"]["alias_robustness"]["downgrade_rate"]
    eligible = {k: v for k, v in table.items()
                if v["alias_robustness"]["downgrade_rate"] <= reference + ROBUSTNESS_MARGIN}
    chosen = max(eligible, key=lambda k: eligible[k]["cv_macro_f1"])
    out = {
        "rule": ("max 5-fold CV macro-F1 on validation among candidates whose alias downgrade rate "
                 f"<= documented hybrid + {ROBUSTNESS_MARGIN}"),
        "fusion_fit": {**fusion, "train_sample_size": int(len(train))},
        "candidates": table,
        "eligible": sorted(eligible),
        "chosen": chosen,
        "validation_balance": class_balance(val),
        "train_sample_balance": class_balance(train),
    }
    SELECTION_FILE.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out


def stage_final(force: bool = False) -> dict:
    if TEST_MARKER.exists() and not force:
        raise SystemExit("The isolated test split was already read by a final run; refusing to read it again.")
    selection = json.loads(SELECTION_FILE.read_text(encoding="utf-8"))
    chosen = selection["chosen"]
    val, test, test_alias = load("validation"), load("test"), load("test_alias")
    y3_val = val["y3"].to_numpy()

    methods = {"hybrid": selection["candidates"][chosen]["weights"], **SINGLE}
    calibration = {}
    for key, weights in methods.items():
        raw_val = raw_score(val, weights)
        c1, c2 = fit_cuts(raw_val, y3_val)
        ceiling = float(max(np.max(raw_val), c2 * 1.05))
        calibration[key] = {"cut_consider": round(c1, 6), "cut_hire": round(c2, 6), "ceiling": round(ceiling, 6),
                            "consider_display": CONSIDER_DISPLAY, "hire_display": HIRE_DISPLAY}

    TEST_MARKER.write_text(date.today().isoformat(), encoding="utf-8")
    report = {"chosen_hybrid_method": chosen, "hybrid_weights": methods["hybrid"],
              "test_balance": class_balance(test), "methods": {}}
    for key, weights in methods.items():
        cal = calibration[key]
        raw = raw_score(test, weights)
        after = verdicts(raw, cal["cut_consider"], cal["cut_hire"])
        before = legacy_product_verdicts(raw)
        report["methods"][key] = {
            "weights": weights,
            "before_product_raw_x100_at_55_75": full_report(test, raw, before),
            "after_calibrated_at_55_75": full_report(test, raw, after),
            "alias_robustness_test": downgrade_rate(test, test_alias, weights,
                                                    (cal["cut_consider"], cal["cut_hire"])),
            "displayed_score_quantiles_after": {
                f"p{q}": float(np.percentile(display(raw, cal["cut_consider"], cal["cut_hire"], cal["ceiling"]), q))
                for q in (0, 10, 25, 50, 75, 90, 100)},
        }
    # Reference reading kept for traceability: the documented hybrid at the
    # experimental binary threshold chosen on validation by the benchmark.
    doc_raw = raw_score(test, DOCUMENTED)
    report["reference_documented_hybrid_at_0_2636"] = binary_report(
        (test["y3"].to_numpy() >= 1).astype(int), (doc_raw >= 0.2636).astype(int))

    dataset_hash = hashlib.sha256(DATASET.read_bytes()).hexdigest()[:16]
    version = f"synthetic-v1-{date.today().isoformat()}"
    payload = {
        "version": version,
        "methods": calibration,
        "provenance": {
            "fitted_on": "validation split of the synthetic benchmark (n=%d), seed 42" % len(val),
            "criterion": "3-class macro-F1 (unrelated / transferable / strong) on validation",
            "hybrid_method": chosen,
            "hybrid_weights": methods["hybrid"],
            "dataset_sha256_16": dataset_hash,
            "warning": "Synthetic labels: not a validated hiring policy. Re-fit on annotated real data.",
        },
    }
    CALIBRATION_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report["calibration"] = payload
    FINAL_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def calibration_payload(hybrid_candidate: str, decision_note: str) -> dict:
    """Calibration from the VALIDATION split only (no test data is read)."""
    selection = json.loads(SELECTION_FILE.read_text(encoding="utf-8"))
    val = load("validation")
    y3_val = val["y3"].to_numpy()
    methods = {"hybrid": selection["candidates"][hybrid_candidate]["weights"], **SINGLE}
    calibration = {}
    for key, weights in methods.items():
        raw_val = raw_score(val, weights)
        c1, c2 = fit_cuts(raw_val, y3_val)
        ceiling = float(max(np.max(raw_val), c2 * 1.05))
        calibration[key] = {"cut_consider": round(c1, 6), "cut_hire": round(c2, 6), "ceiling": round(ceiling, 6),
                            "consider_display": CONSIDER_DISPLAY, "hire_display": HIRE_DISPLAY}
    return {
        "version": f"synthetic-v1-{date.today().isoformat()}" + ("" if hybrid_candidate == selection["chosen"]
                                                                  else f"-{hybrid_candidate.replace('_', '-')}"),
        "methods": calibration,
        "provenance": {
            "fitted_on": "validation split of the synthetic benchmark (n=%d), seed 42" % len(val),
            "criterion": "3-class macro-F1 (unrelated / transferable / strong) on validation",
            "hybrid_method": hybrid_candidate,
            "hybrid_weights": methods["hybrid"],
            "pre_registered_rule_winner": selection["chosen"],
            "product_decision": decision_note,
            "dataset_sha256_16": hashlib.sha256(DATASET.read_bytes()).hexdigest()[:16],
            "warning": "Synthetic labels: not a validated hiring policy. Re-fit on annotated real data.",
        },
    }


def stage_write(hybrid_candidate: str, note: str, out: Path) -> dict:
    payload = calibration_payload(hybrid_candidate, note)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["select", "final", "write"])
    parser.add_argument("--force", action="store_true", help="re-read the test split (logged)")
    parser.add_argument("--hybrid-candidate", default=None, help="write: candidate used for the 'hybrid' key")
    parser.add_argument("--note", default="", help="write: reason recorded in the provenance")
    parser.add_argument("--out", default=str(CALIBRATION_OUT))
    args = parser.parse_args()
    if args.stage == "write":
        print(json.dumps(stage_write(args.hybrid_candidate, args.note, Path(args.out)), indent=2))
        raise SystemExit(0)
    result = stage_select() if args.stage == "select" else stage_final(args.force)
    print(json.dumps(result if args.stage == "select" else {
        k: v for k, v in result.items() if k != "methods"}, indent=2))
