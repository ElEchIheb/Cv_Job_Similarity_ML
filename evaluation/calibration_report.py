"""Before / after comparison tables from the frozen calibration (reporting only).

Reads the selection (train/validation) and the written calibration, then
reports on the isolated test split — with every parameter frozen, nothing is
fitted here:
  * BEFORE  = product as deployed before the fix: documented hybrid 0.2/0.4/0.4,
              displayed score = raw x 100, verdict at 55/75 (with the old
              0-1/0-100 quirk of the DecisionEngine);
  * AFTER   = shipped product: hybrid weights + calibration from score_calibration.json, verdict at 55/75;
  * every other candidate with its own validation cut points (comparison).

This is a complementary read of the test split after the final stage; it does
not change any parameter, which the calibration file hash check enforces.
Usage: python evaluation/calibration_report.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / "evaluation"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from calibration_study import (CALIBRATION_OUT, DOCUMENTED, SELECTION_FILE, downgrade_rate,  # noqa: E402
                               full_report, legacy_product_verdicts, load, raw_score, verdicts)

OUT = ROOT / "evaluation" / "results" / "calibration_report.json"


def main() -> dict:
    cal_bytes = CALIBRATION_OUT.read_bytes()
    calibration = json.loads(cal_bytes)
    selection = json.loads(SELECTION_FILE.read_text(encoding="utf-8"))
    test, test_alias = load("test"), load("test_alias")

    rows = {}
    doc_raw = raw_score(test, DOCUMENTED)
    rows["BEFORE_product_documented_hybrid_raw_x100"] = {
        "weights": DOCUMENTED, **full_report(test, doc_raw, legacy_product_verdicts(doc_raw))}

    hybrid_cal = calibration["methods"]["hybrid"]
    weights = calibration["provenance"]["hybrid_weights"]
    raw = raw_score(test, weights)
    cuts = (hybrid_cal["cut_consider"], hybrid_cal["cut_hire"])
    rows["AFTER_product_shipped_calibrated"] = {
        "weights": weights, "cuts": list(cuts), **full_report(test, raw, verdicts(raw, *cuts)),
        "alias_robustness_test": downgrade_rate(test, test_alias, weights, cuts)}

    for name, cand in selection["candidates"].items():
        r = raw_score(test, cand["weights"])
        c = tuple(cand["cuts"])
        rows[f"candidate_{name}_validation_cuts"] = {
            "weights": cand["weights"], "cuts": list(c), **full_report(test, r, verdicts(r, *c)),
            "alias_robustness_test": downgrade_rate(test, test_alias, cand["weights"], c)}
        rows[f"candidate_{name}_before_raw_x100"] = {
            "weights": cand["weights"], **full_report(test, r, legacy_product_verdicts(r))}

    # Paired bootstrap on the same test pairs: is the selected fusion better
    # than the documented hybrid / TF-IDF alone once each is calibrated?
    y3 = test["y3"].to_numpy()
    preds = {name: verdicts(raw_score(test, cand["weights"]), *cand["cuts"])
             for name, cand in selection["candidates"].items()}
    rng = np.random.default_rng(42)
    from calibration_study import macro_f1
    diffs = {"fusion_learned_minus_hybrid_documented": [], "fusion_learned_minus_tfidf": [],
             "hybrid_documented_minus_tfidf": []}
    for _ in range(2000):
        idx = rng.integers(0, len(y3), len(y3))
        f = {k: macro_f1(y3[idx], v[idx]) for k, v in preds.items()}
        diffs["fusion_learned_minus_hybrid_documented"].append(f["fusion_learned"] - f["hybrid_documented"])
        diffs["fusion_learned_minus_tfidf"].append(f["fusion_learned"] - f["tfidf"])
        diffs["hybrid_documented_minus_tfidf"].append(f["hybrid_documented"] - f["tfidf"])
    paired = {k: {"mean": round(float(np.mean(v)), 4),
                  "ci95": [round(float(np.percentile(v, 2.5)), 4), round(float(np.percentile(v, 97.5)), 4)],
                  "share_le_0": round(float(np.mean(np.asarray(v) <= 0)), 4)} for k, v in diffs.items()}

    out = {"calibration_version": calibration["version"],
           "paired_bootstrap_macro_f1_differences": paired,
           "calibration_sha256_16": hashlib.sha256(cal_bytes).hexdigest()[:16],
           "note": "Frozen parameters; complementary read of the isolated test split, nothing fitted.",
           "rows": rows}
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    assert CALIBRATION_OUT.read_bytes() == cal_bytes
    return out


def table(out: dict) -> str:
    lines = ["| Lecture | Macro-F1 3 classes [IC95] | F1 CONSIDER+ | F1 HIRE | Kappa q. | R / C / H | AUC |",
             "|---|---|---|---|---|---|---|"]
    for name, r in out["rows"].items():
        t, b, h = r["three_class"], r["binary_consider_or_better"], r["binary_hire_vs_strong"]
        ci = r["bootstrap"]["macro_f1_95ci"]
        vc = t["verdict_counts"]
        lines.append(f"| {name} | {t['macro_f1']:.3f} [{ci[0]:.3f}-{ci[1]:.3f}] | {b['f1']:.3f} | {h['f1']:.3f} | "
                     f"{t['quadratic_kappa']:.3f} | {vc['REJECT']} / {vc['CONSIDER']} / {vc['HIRE']} | "
                     f"{r['ranking']['roc_auc']:.3f} |")
    return "\n".join(lines)


if __name__ == "__main__":
    result = main()
    print(table(result))
    print(json.dumps(result["paired_bootstrap_macro_f1_differences"], indent=2))
