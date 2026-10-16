"""Compute and cache the three component scores (TF-IDF, embeddings, skills).

One-off, resumable computation used by the calibration study
(``evaluation/calibration_study.py``). It reproduces the benchmark split of
``EvaluationSuite.stratified_split`` (seed 42) and writes one CSV per subset in
``evaluation/cache/``:

* ``validation``  — the full validation split (used to fit calibration / fusion);
* ``train_sub``   — a stratified sample of the training split (used to fit the
                    learned-fusion candidate only);
* ``test``        — the isolated test split (TF-IDF and skill scores are
                    recomputed and checked against the stored benchmark scores;
                    the stored embedding scores are reused, see below);
* ``validation_alias`` / ``test_alias`` — pairs whose CV was rewritten with
                    skill aliases (e.g. "kubernetes" -> "k8s"), a limited
                    reformulation check (validation for selection, test for
                    the final report).

TF-IDF is fitted on the training split only, exactly like the benchmark. No
label is used by this script except to stratify the training sample.

Usage: python evaluation/compute_components.py [--train-sample 1500]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.evaluation.evaluator import EvaluationSuite  # noqa: E402
from src.models.skill_matcher import SkillMatcher  # noqa: E402
from src.models.tfidf_model import TFIDFMatcher  # noqa: E402

DATASET = ROOT / "data" / "datasets" / "cv_job_dataset.csv"
DICTIONARY = ROOT / "data" / "datasets" / "skills_dictionary.json"
RESULTS = ROOT / "evaluation" / "results" / "evaluation_results.json"
CACHE = ROOT / "evaluation" / "cache"
META_COLS = ["id", "label", "score_raw", "domain", "seniority", "difficulty"]
CHUNK = 100


def language_of(cv_text: str, job_text: str) -> str:
    """The generator writes cross-lingual pairs as an English CV + French offer."""
    return "cross_lingual" if cv_text.startswith("PROFILE\n") else "fr"


def alias_rewrite(text: str, inverse_aliases: dict[str, str]) -> str:
    out = text
    for target, alias in inverse_aliases.items():
        out = re.sub(rf"(?<![\w.+#-]){re.escape(target)}(?![\w.+#-])", alias, out)
    return out


def _frame(part: pd.DataFrame) -> pd.DataFrame:
    frame = part[META_COLS].copy()
    frame["language"] = [language_of(c, j) for c, j in zip(part["cv_text"], part["job_text"])]
    return frame.reset_index(drop=True)


def _embedding_scores(matcher, cvs: list[str], jobs: list[str], tag: str) -> list[float]:
    progress = CACHE / f"{tag}_embedding.partial.json"
    done: list[float] = json.loads(progress.read_text()) if progress.exists() else []
    start = time.perf_counter()
    for i in range(len(done), len(cvs), CHUNK):
        done.extend(float(x) for x in matcher.batch_predict(cvs[i:i + CHUNK], jobs[i:i + CHUNK]))
        progress.write_text(json.dumps(done))
        rate = (time.perf_counter() - start) / max(1, len(done))
        print(f"[{tag}] {len(done)}/{len(cvs)}  {rate:.2f}s/pair", flush=True)
    return done


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-sample", type=int, default=1500)
    args = parser.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATASET)
    split = EvaluationSuite.stratified_split(df)
    print("split sizes:", len(split.train), len(split.validation), len(split.test), flush=True)

    tfidf = TFIDFMatcher().fit_pairs(split.train["cv_text"].tolist(), split.train["job_text"].tolist())
    skill = SkillMatcher()

    train_sub = split.train.groupby("score_raw").sample(
        frac=args.train_sample / len(split.train), random_state=42)

    aliases = json.loads(DICTIONARY.read_text(encoding="utf-8")).get("aliases", {})
    inverse = {}
    for alias, target in aliases.items():
        if alias != target and len(alias) < len(target):
            inverse.setdefault(target, alias)
    def rewritten(part: pd.DataFrame, name: str) -> pd.DataFrame:
        copy = part.copy()
        copy["cv_text"] = [alias_rewrite(t, inverse) for t in copy["cv_text"]]
        changed = copy["cv_text"].to_numpy() != part["cv_text"].to_numpy()
        print(f"alias rewrite changed {int(changed.sum())} {name} CVs", flush=True)
        return copy[changed]

    test_alias = rewritten(split.test, "test")
    validation_alias = rewritten(split.validation, "validation")

    stored = json.loads(RESULTS.read_text(encoding="utf-8"))["metrics"]

    from src.models.embedding_model import EmbeddingMatcher  # heavy import, after cheap checks
    embedding = EmbeddingMatcher()

    jobs = {
        "test": split.test,
        "validation": split.validation,
        "train_sub": train_sub,
        "test_alias": test_alias,
        # Robustness check used for method selection must not come from test.
        "validation_alias": validation_alias,
    }
    for tag, part in jobs.items():
        out = CACHE / f"components_{tag}.csv"
        if out.exists():
            print(f"[{tag}] cached", flush=True)
            continue
        cvs, jbs = part["cv_text"].tolist(), part["job_text"].tolist()
        frame = _frame(part)
        frame["tfidf"] = np.asarray(tfidf.batch_predict(cvs, jbs), dtype=float)
        frame["skill"] = np.asarray(skill.batch_predict(cvs, jbs), dtype=float)
        if tag == "test":
            # The isolated test split was already scored by the benchmark with the
            # same models; check the cheap components match before reusing the
            # stored (expensive) embedding scores instead of recomputing them.
            for name in ("tfidf", "skill"):
                gap = float(np.max(np.abs(frame[name].to_numpy() - np.asarray(stored[name]["scores"]))))
                print(f"[test] max |recomputed - stored| {name} = {gap:.2e}", flush=True)
                if gap > 1e-6:
                    raise SystemExit(f"Stored {name} scores do not match; refusing to reuse embeddings.")
            frame["embedding"] = np.asarray(stored["embedding"]["scores"], dtype=float)
            frame["embedding_source"] = "stored_benchmark"
        else:
            frame["embedding"] = _embedding_scores(embedding, cvs, jbs, tag)
            frame["embedding_source"] = "computed"
        frame.to_csv(out, index=False)
        partial = CACHE / f"{tag}_embedding.partial.json"
        partial.unlink(missing_ok=True)
        print(f"[{tag}] written {out.name} ({len(frame)} rows)", flush=True)


if __name__ == "__main__":
    main()
