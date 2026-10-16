"""Robustness probes for the evidence screening (validation split, frozen parameters).

Each probe modifies validation CVs in a controlled way and compares the verdict
produced by the PREVIOUS pipeline (raw text, bag-of-skills extraction, no
evidence rule) with the CURRENT one (copied-offer removal, negation-aware and
evidence-weighted skills, HIRE withheld when evidence is insufficient). Both use
the shipped calibration (documented hybrid, ``score_calibration.json``).

Probes (seed 42, up to N pairs each):
  P1  unrelated CV + the offer's requirement list copied verbatim in a SKILLS section
  P2  unrelated CV + the same skills, reordered, in a SKILLS section (no verbatim copy)
  P3  unrelated CV + the same skills woven into an experience sentence
  P4  unrelated CV + the whole offer pasted at the end
  P5  unrelated CV + a negated mention ("No professional experience with ...")
  P6  strong CV with half of the matched skills removed (partial profile)
  P7  strong CV made long with unrelated experience paragraphs
  G   genuine validation pairs (no modification)
No parameter is fitted here; the screening constants were fixed beforehand.
Usage: python evaluation/robustness_probes.py [--n 200]
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / "evaluation"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from calibration_study import load  # noqa: E402

OUT = ROOT / "evaluation" / "results" / "robustness_probes.json"
REQ = re.compile(r"(?:Competences obligatoires|Competences requises|Required|Must have):\s*(.*?)\.(?:\s|$)")
CLASSES = ["REJECT", "CONSIDER", "HIRE"]


def legacy_skill_details(extractor, cv: str, job: str) -> dict:
    """Skill component as computed before the evidence screening (bag of skills)."""
    from src.models.skill_matcher import SkillMatcher
    cv_p, job_p = extractor.extract(cv), extractor.extract(job)
    cv_hard, job_hard = set(cv_p["hard_skills"]), set(job_p["hard_skills"])
    cv_soft, job_soft = set(cv_p["soft_skills"]), set(job_p["soft_skills"])
    crit = SkillMatcher._detect_critical_skills(job, job_hard)
    hard = len(cv_hard & job_hard) / len(job_hard) if job_hard else 0.0
    soft = len(cv_soft & job_soft) / len(job_soft) if job_soft else 0.0
    wh, ws = (0.7 if job_hard else 0.0), (0.3 if job_soft else 0.0)
    base = (wh * hard + ws * soft) / (wh + ws) if wh + ws else 0.0
    bonus = 0.05 if cv_p.get("domain") == job_p.get("domain") else 0.0
    certs = min(0.10, 0.03 * len(set(cv_p["certifications"]) & set(job_p["certifications"])))
    pen = 0.20 * len(crit - cv_hard) / len(crit) if crit else 0.0
    return {"score": float(np.clip(base + bonus + certs - pen, 0, 1)), "critical_missing": sorted(crit - cv_hard)}


def main(n: int, only: list[str] | None = None) -> dict:
    from src.decisioning import DecisionEngine
    from src.decisioning.calibration import load_calibration
    from src.evaluation.evaluator import EvaluationSuite
    from src.models.embedding_model import EmbeddingMatcher
    from src.models.skill_matcher import SkillMatcher
    from src.models.tfidf_model import TFIDFMatcher
    from src.nlp.screening import evidence_insufficient, similarity_text

    rng = random.Random(42)
    df = pd.read_csv(ROOT / "data" / "datasets" / "cv_job_dataset.csv")
    split = EvaluationSuite.stratified_split(df)
    val = split.validation.reset_index(drop=True)
    tfidf = TFIDFMatcher().fit_pairs(split.train["cv_text"].tolist(), split.train["job_text"].tolist())
    skill = SkillMatcher()
    embedding = EmbeddingMatcher()
    cal = load_calibration()
    w = cal.provenance["hybrid_weights"]
    engine = DecisionEngine()
    cache = load("validation").set_index("id")

    def verdict(raw: float, critical, gap=None) -> int:
        pct = cal.to_display("hybrid", raw)
        return CLASSES.index(engine.evaluate(pct, critical_missing=critical, evidence_gap=gap).decision)

    def score(cvs, jobs, ids=None):
        """Return (before, after, cap_rate) verdict arrays for modified pairs."""
        screened = [similarity_text(c, j, skill.extractor) for c, j in zip(cvs, jobs)]
        t_b, t_a = tfidf.batch_predict(cvs, jobs), tfidf.batch_predict(screened, jobs)
        e_b = embedding.batch_predict(cvs, jobs)
        e_a = [eb if s == c else None for eb, s, c in zip(e_b, screened, cvs)]
        todo = [i for i, v in enumerate(e_a) if v is None]
        if todo:
            got = embedding.batch_predict([screened[i] for i in todo], [jobs[i] for i in todo])
            for i, v in zip(todo, got):
                e_a[i] = v
        before, after, caps = [], [], 0
        for k, (c, j) in enumerate(zip(cvs, jobs)):
            old = legacy_skill_details(skill.extractor, c, j)
            new = skill.predict_detailed(c, j)
            gap = evidence_insufficient(new)[1] or None
            caps += bool(gap)
            before.append(verdict(w["tfidf"] * t_b[k] + w["embedding"] * e_b[k] + w["skill"] * old["score"],
                                  old["critical_missing"]))
            after.append(verdict(w["tfidf"] * t_a[k] + w["embedding"] * e_a[k] + w["skill"] * new["score"],
                                 new["critical_missing"], gap))
        return np.array(before), np.array(after), caps / max(1, len(cvs))

    unrelated = val[val["score_raw"] == 0.0]
    unrelated = unrelated[[bool(REQ.search(j)) for j in unrelated["job_text"]]].sample(
        n=min(n, len(unrelated)), random_state=42)
    strong = val[val["score_raw"] == 1.0].sample(n=min(n, int((val["score_raw"] == 1.0).sum())), random_state=42)
    req_lists = [REQ.search(j).group(1) for j in unrelated["job_text"]]

    def shuffled(lst: str) -> str:
        items = [s.strip() for s in lst.split(",") if s.strip()]
        rng.shuffle(items)
        return ", ".join(items)

    probes = {
        "P1_verbatim_list_in_skills_section": [f"{c}\n\nSKILLS\n{r}" for c, r in zip(unrelated["cv_text"], req_lists)],
        "P2_reordered_list_in_skills_section": [f"{c}\n\nSKILLS\n{shuffled(r)}" for c, r in zip(unrelated["cv_text"], req_lists)],
        "P3_skills_in_experience_sentence": [f"{c}\n\nEXPERIENCE\nWorked on several projects using {shuffled(r)}."
                                             for c, r in zip(unrelated["cv_text"], req_lists)],
        "P4_whole_offer_pasted": [f"{c}\n\n{j}" for c, j in zip(unrelated["cv_text"], unrelated["job_text"])],
        "P5_negated_mention": [f"{c}\n\nNo professional experience with {shuffled(r)}."
                               for c, r in zip(unrelated["cv_text"], req_lists)],
    }
    report = {"n_per_probe": n, "weights": w, "calibration_version": cal.version, "probes": {}}
    jobs_u = unrelated["job_text"].tolist()
    base_b, _, _ = score(unrelated["cv_text"].tolist(), jobs_u)
    report["unrelated_reference"] = {c: int(np.sum(base_b == i)) for i, c in enumerate(CLASSES)}
    previous = json.loads(OUT.read_text(encoding="utf-8")) if only and OUT.exists() else None
    if previous:
        report["probes"] = previous["probes"]
    for name, cvs in probes.items():
        if only and not any(name.startswith(o) for o in only):
            continue
        b, a, caps = score(cvs, jobs_u)
        report["probes"][name] = {
            "n": len(cvs), "evidence_cap_rate": round(caps, 4),
            "before": {c: int(np.sum(b == i)) for i, c in enumerate(CLASSES)},
            "after": {c: int(np.sum(a == i)) for i, c in enumerate(CLASSES)},
        }
        print(name, report["probes"][name], flush=True)

    # P6 partial profiles: drop half of the CV's matched skills from its text.
    partial = []
    for c, j in zip(strong["cv_text"], strong["job_text"]):
        matched = skill.predict_detailed(c, j)["matching_hard_skills"]
        drop = matched[: len(matched) // 2]
        text = c
        for s in drop:
            text = re.sub(rf"(?<![\w.+#-]){re.escape(s)}(?![\w.+#-])", "", text, flags=re.IGNORECASE)
        partial.append(text)
    long_pad = unrelated["cv_text"].tolist()
    long_cvs = [f"{c}\n\nEXPERIENCE\n" + "\n".join(long_pad[(k + m) % len(long_pad)] for m in range(1, 4))
                for k, c in enumerate(strong["cv_text"])]
    jobs_s = strong["job_text"].tolist()
    ref_b, ref_a, _ = score(strong["cv_text"].tolist(), jobs_s)
    report["strong_reference"] = {"before": {c: int(np.sum(ref_b == i)) for i, c in enumerate(CLASSES)},
                                  "after": {c: int(np.sum(ref_a == i)) for i, c in enumerate(CLASSES)}}
    for name, cvs in (("P6_partial_profile", partial), ("P7_long_cv", long_cvs)):
        if only and not any(name.startswith(o) for o in only):
            continue
        b, a, caps = score(cvs, jobs_s)
        report["probes"][name] = {
            "n": len(cvs), "evidence_cap_rate": round(caps, 4),
            "before": {c: int(np.sum(b == i)) for i, c in enumerate(CLASSES)},
            "after": {c: int(np.sum(a == i)) for i, c in enumerate(CLASSES)},
        }
        print(name, report["probes"][name], flush=True)

    # G: genuine validation pairs — components cached, only skill/evidence recomputed.
    caps, changed = 0, 0
    for _, r in val.iterrows():
        new = skill.predict_detailed(r["cv_text"], r["job_text"])
        gap = evidence_insufficient(new)[1]
        caps += bool(gap)
        c = cache.loc[r["id"]]
        raw = w["tfidf"] * c["tfidf"] + w["embedding"] * c["embedding"] + w["skill"] * new["score"]
        v_new = verdict(raw, new["critical_missing"], gap or None)
        v_old = verdict(w["tfidf"] * c["tfidf"] + w["embedding"] * c["embedding"] + w["skill"] * c["skill"],
                        new["critical_missing"])
        changed += v_new != v_old
    report["genuine_validation"] = {"n": int(len(val)), "evidence_cap_rate": round(caps / len(val), 4),
                                    "verdicts_changed": int(changed)}
    print("genuine", report["genuine_validation"], flush=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=200)
    parser.add_argument("--only", nargs="*", help="re-run only these probes (others kept from the last report)")
    args = parser.parse_args()
    main(args.n, args.only)
