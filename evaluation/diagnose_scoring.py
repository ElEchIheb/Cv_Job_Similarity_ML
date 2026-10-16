"""Reproducible diagnostic of the score -> verdict chain (pre-fix behaviour).

Run:  python evaluation/diagnose_scoring.py  [--json out.json]

Checks, on the stored benchmark test scores and on the production code path:
1. effective scale (quantiles) of every method's score and of the hybrid fusion;
2. what the DecisionEngine does with each method's percentage at 55/75;
3. whether a percentage <= 1 is re-scaled a second time (0-1 / 0-100 ambiguity);
4. that the production checkpoint carries the weights the code believes it uses.
No threshold or weight is chosen here.
"""
from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RESULTS = ROOT / "evaluation" / "results" / "evaluation_results.json"
CHECKPOINT = ROOT / "models" / "checkpoints" / "hybrid.pkl"


def quantiles(values: np.ndarray) -> dict:
    qs = [0, 10, 25, 50, 75, 90, 99, 100]
    return {f"p{q}": round(float(np.percentile(values, q)), 4) for q in qs}


def main() -> dict:
    from src.decisioning.decision_engine import DecisionEngine, DecisionConfig

    report: dict = {}
    metrics = json.loads(RESULTS.read_text(encoding="utf-8"))["metrics"]
    engine = DecisionEngine(DecisionConfig.default())

    # 1-2. Scale of each method and the verdicts the engine would display.
    for name in ("tfidf", "embedding", "skill", "hybrid"):
        raw = np.asarray(metrics[name]["scores"], dtype=float)
        pct = np.round(raw * 100.0, 1)          # what run_evaluation passes on
        verdicts = [engine.evaluate(p).decision for p in pct]
        report[name] = {
            "raw_quantiles": quantiles(raw),
            "share_ge_55pct": round(float(np.mean(pct >= 55)), 4),
            "share_ge_75pct": round(float(np.mean(pct >= 75)), 4),
            "verdicts_at_55_75": {v: verdicts.count(v) for v in ("HIRE", "CONSIDER", "REJECT")},
            # 3. percentages in (0, 1] are multiplied by 100 a second time.
            "pairs_with_pct_in_(0,1]": int(np.sum((pct > 0) & (pct <= 1.0))),
            "hire_from_double_scaling": int(sum(
                1 for p, v in zip(pct, verdicts) if 0 < p <= 1.0 and v == "HIRE")),
        }

    # 3. Direct demonstration on the engine API.
    report["double_scaling_examples"] = {
        f"{p}%": engine.evaluate(p).as_dict()["decision"] for p in (0.5, 0.9, 1.0, 1.1, 55.0)
    }

    # 4. Production checkpoint.
    with open(CHECKPOINT, "rb") as fh:
        hybrid = pickle.load(fh)
    report["checkpoint"] = {
        "weights": hybrid.weights,
        "optimal_threshold": hybrid.optimal_threshold,
        "tfidf_vocabulary_size": len(getattr(hybrid.models["tfidf"].vectorizer, "vocabulary_", {})),
    }
    # Upper bound reachable by the 0.2/0.4/0.4 fusion with the observed component
    # maxima on the test split (component maxima are not reached on the same pair).
    w = hybrid.weights
    report["hybrid_ceiling_from_component_maxima"] = round(
        sum(w[n] * float(np.max(metrics[n]["scores"])) for n in ("tfidf", "embedding", "skill")), 4)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json")
    args = parser.parse_args()
    out = main()
    text = json.dumps(out, indent=2)
    if args.json:
        Path(args.json).write_text(text, encoding="utf-8")
    print(text)
