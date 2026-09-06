"""
frontend/pages/evaluation_metrics.py
NeuralHire — Performance Metrics Page v4.0
No emojis. Recruiter/analyst language. SVG icons.
Technical model names hidden; only human labels shown.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from frontend.styles.theme import ICONS
from frontend.components.ui import (
    page_header, section_label,
    MODEL_LABELS,
)


def render(project_root: Path):
    page_header(
        badge="AI QUALITY CENTER",
        title="AI System",
        highlight="Quality & Reliability",
        subtitle=(
            "Executive quality benchmarks across all evaluation dimensions — "
            "including accuracy, decision reliability, precision, and response latency."
        ),
    )

    results_path = project_root / "evaluation" / "results" / "evaluation_results.json"
    figures_dir  = project_root / "evaluation" / "figures"

    if not results_path.exists():
        _render_no_results(project_root)
        return

    try:
        payload  = json.loads(results_path.read_text(encoding="utf-8"))
        metrics  = payload.get("metrics", {})
        analysis = payload.get("analysis", {})
    except Exception as e:
        st.error(f"Failed to load evaluation results: {e}")
        return

    # ── PROVENANCE (scientific honesty: these are offline benchmark results,
    #    not live metrics recomputed on every visit) ─────────────────────────
    import datetime as _dt
    _mtime = _dt.datetime.fromtimestamp(results_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    _n_samples = payload.get("dataset_size") or payload.get("n_samples") or payload.get("test_size")
    _prov = f"Source: offline evaluation run — {results_path.name}, generated {_mtime}."
    if _n_samples:
        _prov += f" Test set: {_n_samples} pairs."
    st.markdown(f"""
    <div class="nh-alert nh-alert-info" style="margin-bottom:16px;">
      <span class="nh-alert-icon">{ICONS['info']}</span>
      <span style="font-size:0.82rem;">{_prov} These figures reflect the last benchmark
      run on the held-out evaluation dataset — they are not recomputed live and do not
      change with day-to-day recruiter evaluations. Re-run the evaluation suite to refresh them.</span>
    </div>
    """, unsafe_allow_html=True)

    # ── PERFORMANCE SUMMARY TABLE ─────────────────────────────────────────────
    section_label("bar-chart", "MODEL PERFORMANCE SUMMARY")

    summary_rows = []
    best_f1_model = None
    best_f1_val   = -1.0

    for model_name, m in metrics.items():
        f1   = m.get("f1",         0) * 100
        acc  = m.get("accuracy",   0) * 100
        prec = m.get("precision",  0) * 100
        rec  = m.get("recall",     0) * 100
        auc  = m.get("roc_auc",    0)
        ms   = m.get("inference_ms_per_pair", 0)

        if f1 > best_f1_val:
            best_f1_val   = f1
            best_f1_model = model_name

        friendly_name = MODEL_LABELS.get(model_name, MODEL_LABELS.get(model_name.upper(), model_name))
        summary_rows.append({
            "Evaluation Method":  friendly_name,
            "Accuracy":           f"{acc:.1f}%",
            "Precision":          f"{prec:.1f}%",
            "Recall":             f"{rec:.1f}%",
            "F1 Score":           f"{f1:.1f}%",
            "AUC-ROC":            f"{auc:.3f}",
            "Inference (offline, ms/pair)": f"{ms:.1f}",
        })

    df_summary = pd.DataFrame(summary_rows)
    st.dataframe(df_summary, width="stretch", hide_index=True)

    # ── KEY METRIC HIGHLIGHTS ─────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    section_label("award", "KEY HIGHLIGHTS")

    if metrics:
        top_f1     = max(metrics.values(), key=lambda m: m.get("f1", 0))
        top_acc    = max(metrics.values(), key=lambda m: m.get("accuracy", 0))
        top_speed  = min(metrics.values(), key=lambda m: m.get("inference_ms_per_pair", 9999))
        best_name  = MODEL_LABELS.get(best_f1_model, MODEL_LABELS.get((best_f1_model or "").upper(), best_f1_model or "N/A"))

        stat_cards = [
            {"label": "Best Accuracy",    "value": f"{top_acc.get('accuracy', 0)*100:.1f}%", "desc": "Highest classification accuracy", "color": "var(--success)"},
            {"label": "Best F1 Score",    "value": f"{best_f1_val:.1f}%",                    "desc": f"Best balanced precision/recall — {best_name}", "color": "var(--brand)"},
            {"label": "Best AUC-ROC",     "value": f"{top_f1.get('roc_auc', 0):.3f}",        "desc": "Ranking quality (1.0 = perfect)", "color": "var(--brand-2)"},
            {"label": "Fastest Method",   "value": f"{top_speed.get('inference_ms_per_pair', 0):.1f} ms", "desc": "Offline inference latency per CV–job pair (model scoring only — not end-to-end request time)", "color": "var(--warn)"},
        ]

        cols = st.columns(4, gap="medium")
        for col, card in zip(cols, stat_cards):
            col.markdown(f"""
            <div class="nh-stat" style="border-left:3px solid {card['color']};">
              <div class="nh-stat-value" style="font-size:1.7rem;color:{card['color']}!important;">{card['value']}</div>
              <div class="nh-stat-label">{card['label']}</div>
              <div style="font-size:0.72rem;color:var(--text-muted)!important;margin-top:6px;line-height:1.5;">{card['desc']}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── VISUALISATIONS ────────────────────────────────────────────────────────
    figs = list(figures_dir.glob("*.png")) if figures_dir.exists() else []
    if figs:
        st.markdown("<br>", unsafe_allow_html=True)
        section_label("trending-up", "EVALUATION CHARTS")
        cols = st.columns(min(2, len(figs)))
        for i, fig_path in enumerate(figs[:4]):
            with cols[i % len(cols)]:
                label = fig_path.stem.replace("_", " ").title()
                st.markdown(f'<div style="font-size:0.72rem;color:var(--text-muted);font-weight:700;letter-spacing:.1em;margin-bottom:6px;">{label}</div>', unsafe_allow_html=True)
                st.image(str(fig_path), width="stretch")

    # ── TECHNICAL ANALYSIS ────────────────────────────────────────────────────
    if analysis:
        st.markdown("<br>", unsafe_allow_html=True)
        section_label("info", "SCIENTIFIC & STATISTICAL ANALYSIS")
        
        tab1, tab2, tab3 = st.tabs(["  Confidence Intervals  ", "  Subgroup Performance  ", "  Error Analysis  "])
        
        with tab1:
            st.markdown('<div class="nh-text" style="margin-bottom:12px;"><strong>Bootstrap 95% Confidence Intervals (1000 iterations)</strong><br>Ensures metrics are statistically robust and not due to chance.</div>', unsafe_allow_html=True)
            ci_data = analysis.get("bootstrap_ci", {})
            ci_rows = []
            for m_name, metrics_dict in ci_data.items():
                friendly = MODEL_LABELS.get(m_name, m_name.title())
                ci_rows.append({
                    "Model": friendly,
                    "F1 Score": f"[{metrics_dict.get('f1', [0,0])[0]:.2f} - {metrics_dict.get('f1', [0,0])[1]:.2f}]",
                    "AUC-ROC": f"[{metrics_dict.get('roc_auc', [0,0])[0]:.2f} - {metrics_dict.get('roc_auc', [0,0])[1]:.2f}]",
                    "Accuracy": f"[{metrics_dict.get('accuracy', [0,0])[0]:.2f} - {metrics_dict.get('accuracy', [0,0])[1]:.2f}]",
                })
            if ci_rows:
                st.dataframe(pd.DataFrame(ci_rows), width="stretch", hide_index=True)
                
        with tab2:
            st.markdown('<div class="nh-text" style="margin-bottom:12px;"><strong>Performance by segment</strong><br>Model performance (AUC) broken down by the <em>seniority</em> and <em>technical domain</em> labels present in the evaluation dataset. This is a per-segment performance breakdown, <strong>not</strong> a protected-attribute fairness audit — the dataset contains no demographic attributes (gender, age, ethnicity, etc.), so no such fairness metric is computed or claimed.</div>', unsafe_allow_html=True)
            subgroups = analysis.get("subgroup_analysis", {})
            sen_rows = [{"Seniority": k, "Samples": v.get("count", 0), "AUC": f"{v.get('auc', 0):.3f}"} for k, v in subgroups.get("seniority_performance", {}).items()]
            dom_rows = [{"Domain": k, "Samples": v.get("count", 0), "AUC": f"{v.get('auc', 0):.3f}"} for k, v in subgroups.get("domain_performance", {}).items()]

            if not sen_rows and not dom_rows:
                st.info("Subgroup performance unavailable: the evaluation dataset does not contain the required segment metadata.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("##### Performance by Seniority")
                    if sen_rows:
                        st.dataframe(pd.DataFrame(sen_rows), width="stretch", hide_index=True)
                    else:
                        st.caption("No seniority labels in the dataset.")
                with col2:
                    st.markdown("##### Performance by Domain")
                    if dom_rows:
                        st.dataframe(pd.DataFrame(dom_rows), width="stretch", hide_index=True)
                    else:
                        st.caption("No domain labels in the dataset.")

        with tab3:
            st.markdown('<div class="nh-text" style="margin-bottom:12px;"><strong>Error Analysis (Hybrid Model)</strong><br>Statistical breakdown of misclassifications.</div>', unsafe_allow_html=True)
            err = analysis.get("error_analysis", {})
            _fp_dom = err.get("dominant_fp_domain")
            _fn_dom = err.get("dominant_fn_domain")
            _fp_line = f'<div style="font-size:0.75rem;color:var(--text-muted);">Most common domain: {_fp_dom}</div>' if _fp_dom else ""
            _fn_line = f'<div style="font-size:0.75rem;color:var(--text-muted);">Most common domain: {_fn_dom}</div>' if _fn_dom else ""
            st.markdown(f"""
            <div style="display:flex; gap:20px;">
                <div class="nh-stat" style="border-left:3px solid var(--danger);">
                    <div class="nh-stat-value" style="font-size:1.4rem;color:var(--danger)!important;">{err.get("fp_count", 0)}</div>
                    <div class="nh-stat-label">False Positives</div>
                    {_fp_line}
                </div>
                <div class="nh-stat" style="border-left:3px solid var(--brand-2);">
                    <div class="nh-stat-value" style="font-size:1.4rem;color:var(--brand-2)!important;">{err.get("fn_count", 0)}</div>
                    <div class="nh-stat-label">False Negatives</div>
                    {_fn_line}
                </div>
            </div>
            """, unsafe_allow_html=True)


def _render_no_results(project_root: Path):
    st.markdown(f"""
    <div class="nh-empty" style="margin-top:32px;">
      <div class="nh-empty-icon">{ICONS['trending-up']}</div>
      <div class="nh-empty-title">No benchmark results available yet</div>
      <div class="nh-empty-desc">
        Run the evaluation suite to generate performance metrics.
      </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("How to run the evaluation"):
        st.code(
            "python -m evaluation.run_evaluation --output evaluation/results/",
            language="bash",
        )
