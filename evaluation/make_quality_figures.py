"""Regenerate the evaluation figures from versioned results only.

Nothing is fitted or tuned here. Inputs:
  - evaluation/results/calibration_report.json  (3-class verdicts, frozen parameters)
  - evaluation/cache/components_test.csv         (per-pair raw sub-scores of the
    isolated synthetic test split, already read by the calibration study)
  - models/checkpoints/score_calibration.json    (shipped calibration anchors)

The script checks that the cached sub-scores reproduce the confusion matrix of
the report before drawing anything, so the figures cannot drift from the tables.

Outputs (English, served by the AI Quality Center):  evaluation/figures/*.png
Outputs (French, thesis):  ISI-LaTeX-Template-master/.../img/ai/eval_*.png

Usage: python evaluation/make_quality_figures.py
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import roc_auc_score, roc_curve  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "evaluation" / "results"
OUT_EN = ROOT / "evaluation" / "figures"
OUT_FR = ROOT / "ISI-LaTeX-Template-master" / "ISI-LaTeX-Template-master" / "img" / "ai"
WEIGHTS = {"tfidf": 0.2, "embedding": 0.4, "skill": 0.4}
METHOD_COLORS = {"hybrid": "#5b4bc4", "tfidf": "#1f77b4", "embedding": "#e08214", "skill": "#2a9d55"}
VERDICT_COLORS = {"REJECT": "#c0392b", "CONSIDER": "#e3a21a", "HIRE": "#2a9d55"}

TEXT = {
    "en": {
        "methods": {"hybrid": "Hybrid 0.2/0.4/0.4 (shipped)", "tfidf": "TF-IDF", "embedding": "Embeddings", "skill": "Skills"},
        "classes": ["Unrelated", "Transferable", "Strong fit"],
        "verdicts": ["REJECT", "CONSIDER", "HIRE"],
        "cm_title": "Shipped configuration: displayed verdict vs synthetic class",
        "cm_x": "Verdict displayed (calibrated score, 55 / 75)",
        "cm_y": "Synthetic class (generator label)",
        "cm_note": "Isolated synthetic test split, n = {n}. Row % in brackets.",
        "dist_title": "Verdicts on the synthetic test split (n = {n})",
        "dist_groups": ["Synthetic classes\n(reference)","Shipped hybrid\n(calibrated)", "TF-IDF alone\n(calibrated)"],
        "dist_y": "Number of pairs",
        "dist_ref": ["Unrelated", "Transferable", "Strong fit"],
        "roc_title": "Ranking quality of the raw scores (binary: unrelated vs. other)",
        "roc_x": "False positive rate", "roc_y": "True positive rate",
        "roc_note": "AUC measures ranking only; it says nothing about the verdict thresholds.",
        "box_title": "Hybrid raw score by synthetic class, with calibration anchors",
        "box_x": "Hybrid raw score (0-1)",
        "box_anchor": "raw {raw:.3f} → {disp:.0f}/100",
        "box_note": "The calibration maps these raw cut points to 55 and 75 on the displayed scale.",
        "files": {"cm": "verdict_confusion_matrix.png", "dist": "verdict_distribution.png",
                  "roc": "raw_score_roc.png", "box": "hybrid_raw_score_by_class.png"},
    },
    "fr": {
        "methods": {"hybrid": "Hybride 0,2/0,4/0,4 (livré)", "tfidf": "TF-IDF", "embedding": "Embeddings", "skill": "Compétences"},
        "classes": ["Sans rapport", "Transférable", "Adéquation forte"],
        "verdicts": ["REJECT", "CONSIDER", "HIRE"],
        "cm_title": "Version livrée : verdict affiché selon la classe synthétique",
        "cm_x": "Verdict affiché (score calibré, bornes 55 / 75)",
        "cm_y": "Classe synthétique (étiquette du générateur)",
        "cm_note": "Test synthétique isolé, n = {n}. Pourcentage de la ligne entre crochets.",
        "dist_title": "Verdicts sur le test synthétique (n = {n})",
        "dist_groups": ["Classes synthétiques\n(référence)","Hybride livré\n(calibré)", "TF-IDF seul\n(calibré)"],
        "dist_y": "Nombre de paires",
        "dist_ref": ["Sans rapport", "Transférable", "Adéquation forte"],
        "roc_title": "Qualité du classement des scores bruts (binaire : sans rapport / autres)",
        "roc_x": "Taux de faux positifs", "roc_y": "Taux de vrais positifs",
        "roc_note": "L'AUC mesure le classement seul ; elle ne dit rien des bornes des verdicts.",
        "box_title": "Score brut de l'hybride par classe synthétique et ancrages de calibration",
        "box_x": "Score brut de l'hybride (0-1)",
        "box_anchor": "brut {raw:.3f} → {disp:.0f}/100",
        "box_note": "La calibration ramène ces deux valeurs brutes à 55 et 75 sur l'échelle affichée.",
        "files": {"cm": "eval_confusion_verdicts.png", "dist": "eval_verdict_distribution.png",
                  "roc": "eval_roc_raw.png", "box": "eval_hybrid_raw_by_class.png"},
    },
}


def fmt(x: float, lang: str, nd: int = 2) -> str:
    s = f"{x:.{nd}f}"
    return s.replace(".", ",") if lang == "fr" else s


def load():
    report = json.loads((RESULTS / "calibration_report.json").read_text(encoding="utf-8"))
    calib = json.loads((ROOT / "models" / "checkpoints" / "score_calibration.json").read_text(encoding="utf-8"))
    if report["calibration_version"] != calib["version"]:
        raise SystemExit("calibration_report.json does not match the shipped calibration: re-run the report first.")
    comp = pd.read_csv(ROOT / "evaluation" / "cache" / "components_test.csv")
    comp["hybrid"] = sum(w * comp[k] for k, w in WEIGHTS.items())
    comp["cls"] = comp["score_raw"].map({0.0: 0, 0.5: 1, 1.0: 2})
    cut = calib["methods"]["hybrid"]
    pred = np.where(comp["hybrid"] >= cut["cut_hire"], 2, np.where(comp["hybrid"] >= cut["cut_consider"], 1, 0))
    cm = pd.crosstab(comp["cls"], pred).reindex(index=[0, 1, 2], columns=[0, 1, 2], fill_value=0).values.tolist()
    expected = report["rows"]["AFTER_product_shipped_calibrated"]["three_class"]["confusion_matrix_rows_true_cols_pred"]
    if cm != expected:
        raise SystemExit(f"Cached components do not reproduce the report: {cm} != {expected}")
    return report, calib, comp


def fig_confusion(report, lang, out):
    t = TEXT[lang]
    cm = np.array(report["rows"]["AFTER_product_shipped_calibrated"]["three_class"]["confusion_matrix_rows_true_cols_pred"])
    n = int(cm.sum())
    share = cm / cm.sum(axis=1, keepdims=True)
    fig, ax = plt.subplots(figsize=(7.2, 5.2), dpi=200)
    ax.imshow(share, cmap="Blues", vmin=0, vmax=1)
    for i in range(3):
        for j in range(3):
            ax.text(j, i, f"{cm[i, j]}\n[{fmt(100 * share[i, j], lang, 0)} %]", ha="center", va="center",
                    fontsize=12, color="white" if share[i, j] > 0.55 else "#1a1a1a")
    ax.set_xticks(range(3), t["verdicts"])
    ax.set_yticks(range(3), [f"{c}\n(n = {cm[i].sum()})" for i, c in enumerate(t["classes"])])
    ax.set_xlabel(t["cm_x"])
    ax.set_ylabel(t["cm_y"])
    ax.set_title(t["cm_title"], fontsize=11)
    fig.text(0.5, 0.01, t["cm_note"].format(n=n), ha="center", fontsize=8.5, color="#444")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def fig_distribution(report, lang, out):
    t = TEXT[lang]
    rows = report["rows"]
    after = rows["AFTER_product_shipped_calibrated"]["three_class"]
    n = sum(after["per_class"][c]["support"] for c in ("REJECT", "CONSIDER", "HIRE"))
    ref = [after["per_class"][c]["support"] for c in ("REJECT", "CONSIDER", "HIRE")]
    series = [
        ref,
        [after["verdict_counts"][c] for c in ("REJECT", "CONSIDER", "HIRE")],
        [rows["candidate_tfidf_validation_cuts"]["three_class"]["verdict_counts"][c] for c in ("REJECT", "CONSIDER", "HIRE")],
    ]
    fig, ax = plt.subplots(figsize=(8.6, 4.6), dpi=200)
    x = np.arange(len(series))
    width = 0.26
    for k, verdict in enumerate(("REJECT", "CONSIDER", "HIRE")):
        vals = [s[k] for s in series]
        bars = ax.bar(x + (k - 1) * width, vals, width, color=VERDICT_COLORS[verdict],
                      label=f"{verdict} / {t['dist_ref'][k]}" if lang else verdict)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 15, str(v), ha="center", fontsize=8)
    ax.set_xticks(x, t["dist_groups"], fontsize=9)
    ax.set_ylabel(t["dist_y"])
    ax.set_ylim(0, max(max(s) for s in series) * 1.12)
    ax.set_title(t["dist_title"].format(n=n), fontsize=11)
    ax.legend(fontsize=8.5, frameon=False, loc="upper right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def fig_roc(comp, lang, out):
    t = TEXT[lang]
    y = (comp["cls"] > 0).astype(int)
    fig, ax = plt.subplots(figsize=(6.4, 5.2), dpi=200)
    for m in ("hybrid", "tfidf", "skill", "embedding"):
        fpr, tpr, _ = roc_curve(y, comp[m])
        auc = roc_auc_score(y, comp[m])
        ax.plot(fpr, tpr, color=METHOD_COLORS[m], lw=2.2 if m == "hybrid" else 1.4,
                label=f"{t['methods'][m]} (AUC = {fmt(auc, lang, 3)})")
    ax.plot([0, 1], [0, 1], ls="--", color="#999", lw=1)
    ax.set_xlabel(t["roc_x"])
    ax.set_ylabel(t["roc_y"])
    ax.set_title(t["roc_title"], fontsize=10.5)
    ax.legend(fontsize=8.5, loc="lower right", frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.5, 0.005, t["roc_note"] + f" n = {len(comp)}.", ha="center", fontsize=8, color="#444")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def fig_box(comp, calib, lang, out):
    t = TEXT[lang]
    cut = calib["methods"]["hybrid"]
    data = [comp.loc[comp["cls"] == k, "hybrid"].values for k in (0, 1, 2)]
    fig, ax = plt.subplots(figsize=(8.0, 4.0), dpi=200)
    bp = ax.boxplot(data, vert=False, widths=0.55, patch_artist=True, showfliers=True,
                    flierprops={"markersize": 2.5, "alpha": 0.5})
    for patch, col in zip(bp["boxes"], ("#e8b4ad", "#f3d79a", "#a9d8b8")):
        patch.set_facecolor(col)
    ax.set_yticks([1, 2, 3], [f"{c} (n = {len(d)})" for c, d in zip(t["classes"], data)])
    for raw, disp, col, ha, dx in ((cut["cut_consider"], cut["consider_display"], VERDICT_COLORS["CONSIDER"], "right", -0.004),
                                   (cut["cut_hire"], cut["hire_display"], VERDICT_COLORS["HIRE"], "left", 0.004)):
        ax.axvline(raw, color=col, ls="--", lw=1.6)
        label = t["box_anchor"].format(raw=raw, disp=disp)
        ax.text(raw + dx, 3.48, label.replace(".", ",") if lang == "fr" else label, color=col, fontsize=8.5, ha=ha)
    ax.set_ylim(0.5, 3.7)
    ax.set_xlabel(t["box_x"])
    ax.set_title(t["box_title"], fontsize=10.5, pad=14)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.5, 0.005, t["box_note"], ha="center", fontsize=8, color="#444")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    report, calib, comp = load()
    for lang, out_dir in (("en", OUT_EN), ("fr", OUT_FR)):
        out_dir.mkdir(parents=True, exist_ok=True)
        f = TEXT[lang]["files"]
        fig_confusion(report, lang, out_dir / f["cm"])
        fig_distribution(report, lang, out_dir / f["dist"])
        fig_roc(comp, lang, out_dir / f["roc"])
        fig_box(comp, calib, lang, out_dir / f["box"])
    manifest = {
        "calibration_version": calib["version"],
        "source": ["evaluation/results/calibration_report.json", "evaluation/cache/components_test.csv"],
        "n_test_pairs": int(len(comp)),
        "figures": TEXT["en"]["files"],
    }
    (OUT_EN / "figures_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
