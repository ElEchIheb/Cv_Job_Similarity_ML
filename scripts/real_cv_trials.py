"""Replay the author's real-data trial with the FINAL engine (aggregates only).

Trial replayed: the author's own two CVs, evaluated in September 2026 against the
detailed real "Frontend Dev" offer (offer id 2) of the local development database
``data/jobtest.db`` (git-ignored, never published). The CV texts are read from that
database and scored in-process with the shipped hybrid model, calibration and
DecisionEngine. No LLM call is made and nothing leaves the machine.

Only aggregates are written: raw / calibrated score, verdict, component scores,
skill counts, evidence flag, detected domains, determinism and latency.
No name, contact detail or CV text is printed or stored.
There is no independent recruiter judgement for this offer: no precision,
recall or F1 is computed.

Outputs:
  evaluation/results/real_cv_trials.json
  ISI-LaTeX-Template-master/ISI-LaTeX-Template-master/img/ai/real_cv_scores.png
Usage: python scripts/real_cv_trials.py
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("LLM_ENABLED", "false")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DB = ROOT / "data" / "jobtest.db"
OFFER_ID = 2
CV_IDS = {"CV réel A": 28, "CV réel B": 29}
OUT_JSON = ROOT / "evaluation" / "results" / "real_cv_trials.json"
OUT_FIG = ROOT / "ISI-LaTeX-Template-master" / "ISI-LaTeX-Template-master" / "img" / "ai" / "real_cv_scores.png"


def main() -> None:
    from src.matching.service import MODEL_VERSION, run_evaluation
    from src.models.model_loader import load_production_models
    from src.nlp.screening import evidence_insufficient

    con = sqlite3.connect(DB)
    title, desc, req = con.execute(
        "select title, description, required_skills_raw from job_offers where id=?", (OFFER_ID,)).fetchone()
    job_text = f"{title}\n\n{desc}\n\nRequired Skills: {req}"  # same text as ui._job_text
    models = load_production_models()

    rows = {}
    for label, cv_id in CV_IDS.items():
        cv_text = con.execute("select content_text from cvs where id=?", (cv_id,)).fetchone()[0]
        first = run_evaluation(models, cv_text, job_text, "hybrid")
        t0 = time.perf_counter()
        ev = run_evaluation(models, cv_text, job_text, "hybrid")
        ms = (time.perf_counter() - t0) * 1000
        r, sd, d = ev["result"], ev["result"]["skill_details"], ev["decision"]
        flagged, reason = evidence_insufficient(sd)
        rows[label] = {
            "raw_score": r["raw_score"],
            "displayed_score": r["percentage"],
            "decision": d.decision,
            "components": r["component_scores"],
            "required_skills_found": len(sd["matching_skills"]),
            "required_skills_missing": len(sd["missing_skills"]),
            "critical_missing": len(sd["critical_missing"]),
            "evidence_insufficient": bool(flagged),
            "evidence_reason": reason,
            "cv_domain": sd.get("cv_domain"),
            "job_domain": sd.get("job_domain"),
            "recommendations": len(ev["recommendations"]),
            "deterministic": first["result"]["raw_score"] == r["raw_score"],
            "latency_ms_warm": round(ms, 1),
        }

    report = {
        "date": date.today().isoformat(),
        "model_version": MODEL_VERSION,
        "calibration_version": models["calibration"].version_for("hybrid") if models.get("calibration") else None,
        "offer": {"title": title},
        "note": "Author's own CVs vs one real offer; no reference judgement, no precision/F1.",
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    draw(rows)
    print(json.dumps(report, indent=2, ensure_ascii=False))


def draw(rows: dict) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    labels = ["TF-IDF", "Embeddings", "Compétences", "Score brut\nhybride"]
    keys = ["tfidf_score", "embedding_score", "skill_score"]
    fig, ax = plt.subplots(figsize=(8.4, 4.4), dpi=200)
    x = np.arange(len(labels))
    width = 0.36
    colors = ["#2f5d9e", "#e08a2e"]
    for k, (name, row) in enumerate(rows.items()):
        vals = [row["components"][c] for c in keys] + [row["raw_score"]]
        bars = ax.bar(x + (k - 0.5) * width, vals, width, color=colors[k],
                      label=f"{name} : {row['displayed_score']:.1f}/100, {row['decision']}".replace(".", ","))
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.01, f"{v:.2f}".replace(".", ","), ha="center", fontsize=8)
    ax.set_xticks(x, labels, fontsize=9)
    ax.set_ylabel("Score (0-1)")
    ax.set_ylim(0, 0.6)
    ax.set_title("Mes deux CV face à l'offre réelle « Frontend Dev » (version finale)", fontsize=11)
    ax.legend(fontsize=8.5, frameon=False, loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.5, -0.02, "Pondération 0,2 / 0,4 / 0,4 ; score affiché après calibration ; aucune donnée personnelle affichée.",
             ha="center", fontsize=7.5, color="#555")
    fig.tight_layout()
    fig.savefig(OUT_FIG, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
