"""Keyword-stuffing probe on the VALIDATION split (diagnostic, not used to select).

For every "unrelated" validation pair (generator class 0.0), the offer's list of
required skills is appended verbatim to the CV, as a candidate copying the
offer would do. The probe reports, for each candidate scoring method with its
validation cut points, the share of these unrelated profiles that are promoted
to CONSIDER or HIRE. Lower is more robust.

Usage: python evaluation/stuffing_probe.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / "evaluation"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from calibration_study import COMPONENTS, SELECTION_FILE, load, raw_score, verdicts  # noqa: E402

PATTERN = re.compile(r"(?:Competences obligatoires|Competences requises|Required|Must have):\s*(.*?)\.(?:\s|$)")
OUT = ROOT / "evaluation" / "results" / "stuffing_probe_validation.json"
CACHE = ROOT / "evaluation" / "cache" / "components_validation_stuffed.csv"


def main() -> dict:
    from src.evaluation.evaluator import EvaluationSuite
    from src.models.skill_matcher import SkillMatcher
    from src.models.tfidf_model import TFIDFMatcher

    df = pd.read_csv(ROOT / "data" / "datasets" / "cv_job_dataset.csv")
    split = EvaluationSuite.stratified_split(df)
    unrelated = split.validation[split.validation["score_raw"] == 0.0].copy()
    required = [PATTERN.search(job) for job in unrelated["job_text"]]
    unrelated = unrelated[[m is not None for m in required]]
    stuffed = [f"{cv}\n\nSKILLS\n{m.group(1)}" for cv, m in zip(unrelated["cv_text"], filter(None, required))]

    if CACHE.exists():
        frame = pd.read_csv(CACHE)
    else:
        tfidf = TFIDFMatcher().fit_pairs(split.train["cv_text"].tolist(), split.train["job_text"].tolist())
        from src.models.embedding_model import EmbeddingMatcher
        jobs = unrelated["job_text"].tolist()
        frame = pd.DataFrame({
            "id": unrelated["id"].to_numpy(),
            "tfidf": tfidf.batch_predict(stuffed, jobs),
            "skill": SkillMatcher().batch_predict(stuffed, jobs),
            "embedding": EmbeddingMatcher().batch_predict(stuffed, jobs),
        })
        frame.to_csv(CACHE, index=False)

    selection = json.loads(SELECTION_FILE.read_text(encoding="utf-8"))
    base = load("validation").set_index("id").loc[frame["id"]]
    report = {"n_unrelated_pairs": int(len(frame)), "methods": {}}
    for name, cand in selection["candidates"].items():
        w, cuts = cand["weights"], cand["cuts"]
        before = verdicts(raw_score(base.reset_index(), w), *cuts)
        after = verdicts(raw_score(frame, w), *cuts)
        report["methods"][name] = {
            "weights": w,
            "promoted_before_stuffing": round(float(np.mean(before >= 1)), 4),
            "consider_or_better_after": round(float(np.mean(after >= 1)), 4),
            "hire_after": round(float(np.mean(after == 2)), 4),
        }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
