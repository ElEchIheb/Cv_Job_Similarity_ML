"""
frontend/pages/model_comparison.py
NeuralHire — AI Model Comparison Page v4.0
No emojis. Recruiter language. Technical names hidden behind friendly labels.
"""
from __future__ import annotations

import time
from typing import Callable, Dict, List

import pandas as pd
import streamlit as st

from frontend.styles.theme import ICONS
from frontend.components.ui import (
    page_header, section_label,
    draw_model_comparison_chart,
    MODEL_LABELS, MODEL_DESCRIPTIONS, MODEL_ICONS, MODEL_COLORS, MODEL_ICON_VARIANTS,
)

_MODEL_KEYS = ["HYBRID", "EMBEDDING", "TFIDF", "SKILL"]

# Internal key → run_match model arg
_MODEL_ARG = {"HYBRID": "hybrid", "EMBEDDING": "embedding", "TFIDF": "tfidf", "SKILL": "skill"}


def render(run_match_fn: Callable):
    page_header(
        badge="AI INSIGHTS & EXPLAINABILITY",
        title="AI Evaluation",
        highlight="Insights",
        subtitle=(
            "Compare all four evaluation dimensions side-by-side on the same input "
            "to understand candidate fit from keyword relevance to deep semantic understanding."
        ),
    )

    # ── INPUT ─────────────────────────────────────────────────────────────────
    col_cv, col_jd = st.columns(2, gap="large")
    with col_cv:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
          <div style="width:7px;height:7px;border-radius:50%;background:var(--brand);box-shadow:0 0 7px var(--brand);"></div>
          <span style="font-size:0.65rem;font-weight:700;color:var(--text-muted);letter-spacing:.14em;text-transform:uppercase;">CANDIDATE CV</span>
        </div>
        """, unsafe_allow_html=True)
        cv_text = st.text_area(
            "CV", height=230,
            label_visibility="collapsed",
            placeholder="Paste the candidate's CV here.",
        )
    with col_jd:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
          <div style="width:7px;height:7px;border-radius:50%;background:var(--brand-2);box-shadow:0 0 7px var(--brand-2);"></div>
          <span style="font-size:0.65rem;font-weight:700;color:var(--text-muted);letter-spacing:.14em;text-transform:uppercase;">JOB DESCRIPTION</span>
        </div>
        """, unsafe_allow_html=True)
        jd_text = st.text_area(
            "JD", height=230,
            label_visibility="collapsed",
            placeholder="Paste the job description here.",
        )

    st.markdown("<br>", unsafe_allow_html=True)
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        run_all = st.button("Compare All Methods", width="stretch", key="compare_btn")

    if not run_all:
        return

    if not cv_text.strip() or not jd_text.strip():
        st.error("Please provide both a CV and a job description.")
        return

    # ── RUN ALL MODELS ────────────────────────────────────────────────────────
    rows: List[Dict] = []
    progress = st.progress(0, text="Running evaluations…")

    for i, model_key in enumerate(_MODEL_KEYS):
        progress.progress((i + 1) / len(_MODEL_KEYS), text=f"Running {MODEL_LABELS.get(model_key, model_key)}…")
        t0 = time.time()
        try:
            payload = run_match_fn(cv_text, jd_text, model=_MODEL_ARG[model_key])
            elapsed = round((time.time() - t0) * 1000)
            pct     = payload["result"]["percentage"]
            conf    = payload["result"].get("confidence", "N/A")
            rows.append({
                "Model":     model_key,
                "Score (%)": pct,
                "Speed":     f"{elapsed} ms",
                "Confidence":conf.title() if isinstance(conf, str) else str(conf),
                "_payload":  payload,
            })
        except Exception as exc:
            rows.append({"Model": model_key, "Score (%)": 0, "Speed": "N/A", "Confidence": "Error", "_payload": None})

    progress.empty()

    # ── COMPARISON CHART ──────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    section_label("bar-chart", "SCORE COMPARISON")
    draw_model_comparison_chart([r for r in rows if r["Score (%)"] > 0])

    # ── MODEL CARDS ───────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    section_label("layers", "DETAILED RESULTS")
    cols = st.columns(4, gap="medium")

    for col, row in zip(cols, rows):
        model_key = row["Model"]
        pct       = row["Score (%)"]
        color     = MODEL_COLORS.get(model_key, "var(--brand)")
        icon_key  = MODEL_ICONS.get(model_key, "activity")
        icon_var  = MODEL_ICON_VARIANTS.get(model_key, "brand")
        label     = MODEL_LABELS.get(model_key, model_key)
        desc      = MODEL_DESCRIPTIONS.get(model_key, "")

        if pct >= 75:   tier, tier_col = "Strong Fit",    "var(--success)"
        elif pct >= 55: tier, tier_col = "Potential Fit", "var(--warn)"
        else:           tier, tier_col = "Low Fit",       "var(--danger)"

        col.markdown(f"""
        <div class="nh-model-card">
          <div class="nh-feature-icon {icon_var}" style="margin:0 auto 12px;width:40px;height:40px;">
            {ICONS.get(icon_key,'')}
          </div>
          <div style="font-family:'Space Grotesk',sans-serif;font-size:0.88rem;font-weight:700;
                      color:var(--text-primary)!important;margin-bottom:4px;letter-spacing:-0.02em;">{label}</div>
          <div style="font-size:2.2rem;font-weight:700;font-family:'Space Grotesk',sans-serif;
                      color:{color};letter-spacing:-0.07em;margin:10px 0 4px;">{pct:.0f}%</div>
          <div style="font-size:0.7rem;color:{tier_col};font-weight:700;letter-spacing:.08em;margin-bottom:10px;">{tier}</div>
          <div style="display:flex;justify-content:space-between;font-size:0.68rem;
                      color:var(--text-muted);padding-top:10px;border-top:1px solid var(--border);">
            <span>Speed: {row['Speed']}</span>
            <span>Conf: {row['Confidence']}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── SUMMARY TABLE ─────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    section_label("search", "COMPARISON TABLE")
    df = pd.DataFrame([
        {
            "Evaluation Method": MODEL_LABELS.get(r["Model"], r["Model"]),
            "Score":             f"{r['Score (%)']:.1f}%",
            "Assessment":        ("Strong Fit" if r["Score (%)"]>=75 else "Potential Fit" if r["Score (%)"]>=55 else "Low Fit"),
            "Speed":             r["Speed"],
            "Confidence":        r["Confidence"],
        }
        for r in rows
    ])
    st.dataframe(df, width="stretch", hide_index=True)

    # ── METHOD EXPLAINERS ─────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    section_label("info", "HOW EACH METHOD WORKS")
    exp_cols = st.columns(4, gap="medium")
    for col, model_key in zip(exp_cols, _MODEL_KEYS):
        icon_key = MODEL_ICONS.get(model_key, "activity")
        icon_var = MODEL_ICON_VARIANTS.get(model_key, "brand")
        label    = MODEL_LABELS.get(model_key, model_key)
        desc     = MODEL_DESCRIPTIONS.get(model_key, "")
        color    = MODEL_COLORS.get(model_key, "var(--brand)")

        col.markdown(f"""
        <div class="nh-card nh-card-sm" style="border-left:3px solid {color};">
          <div style="font-family:'Space Grotesk',sans-serif;font-size:0.82rem;font-weight:700;
                      color:var(--text-primary)!important;margin-bottom:8px;">{ICONS.get(icon_key,'')} {label}</div>
          <div style="font-size:0.74rem;color:var(--text-muted)!important;line-height:1.65;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
