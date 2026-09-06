"""
frontend/pages/ranking.py
NeuralHire — Talent Ranking Page v4.0
No emojis. Recruiter language. SVG icons.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import List, Dict

import pandas as pd
import streamlit as st

from frontend.styles.theme import ICONS
from frontend.components.ui import (
    page_header, section_label, ranking_card,
    draw_ranking_chart, stat_row, decision_from_score,
)


def _extract(path: str, suffix: str, pdf_fn, docx_fn) -> str:
    return pdf_fn(path) if suffix == ".pdf" else docx_fn(path)


def render(run_match_fn, extract_pdf_fn, extract_docx_fn):
    page_header(
        badge="TALENT LEADERBOARD",
        title="Talent",
        highlight="Leaderboard",
        subtitle=(
            "Upload multiple CVs and a single job description. "
            "NeuralHire ranks every candidate by AI compatibility score "
            "with a full skill breakdown and hire decision for each."
        ),
    )

    from src.database import SessionLocal
    from src import models_db
    
    db = SessionLocal()
    try:
        active_jobs = db.query(models_db.JobOffer).filter(models_db.JobOffer.status.in_(["OPEN", "ON_HOLD"])).order_by(models_db.JobOffer.id.desc()).all()
        job_options = {j.id: f"[{j.job_code}] {j.title}" for j in active_jobs}
    finally:
        db.close()

    # ── JOB DESCRIPTION INPUT ─────────────────────────────────────────────────
    section_label("briefcase", "JOB DESCRIPTION")
    
    selected_job_id = st.selectbox(
        "Select Job Offer *",
        options=[None] + list(job_options.keys()),
        format_func=lambda x: job_options[x] if x else "— Select a Job Offer —"
    )
    
    job_text = ""
    shared_job_title = "Ranking Position"
    if selected_job_id:
        db = SessionLocal()
        try:
            job = db.query(models_db.JobOffer).filter(models_db.JobOffer.id == selected_job_id).first()
            if job:
                job_text = f"{job.title}\n\n{job.description}\n\nRequired Skills: {job.required_skills_raw}"
                shared_job_title = job.title
        finally:
            db.close()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── CV UPLOAD ─────────────────────────────────────────────────────────────
    section_label("upload", "CANDIDATE CVs")
    st.markdown(f"""
    <div style="font-size:0.78rem;color:var(--text-muted);margin-bottom:8px;">
      {ICONS['info']} &nbsp;Upload multiple PDF or DOCX files — one per candidate.
    </div>
    """, unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Upload CVs",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files:
        st.markdown(f"""
        <div class="nh-alert nh-alert-info" style="margin:10px 0;">
          <span class="nh-alert-icon">{ICONS['info']}</span>
          <span>{len(uploaded_files)} CV{'s' if len(uploaded_files)!=1 else ''} loaded — ready to evaluate.</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── RANK BUTTON ───────────────────────────────────────────────────────────
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        run_rank = st.button("Rank All Candidates", width="stretch", key="rank_btn")

    if not run_rank:
        if not uploaded_files:
            st.markdown("""
            <div class="nh-empty" style="margin-top:32px;">
              <div class="nh-empty-icon"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg></div>
              <div class="nh-empty-title">No candidates added yet</div>
              <div class="nh-empty-desc">Upload CVs above, then click "Rank All Candidates" to start the evaluation.</div>
            </div>
            """, unsafe_allow_html=True)
        return

    # ── VALIDATION ────────────────────────────────────────────────────────────
    if not selected_job_id:
        st.error("Please select a job offer before ranking.")
        return

    if not uploaded_files:
        st.error("Please upload at least one CV.")
        return

    # ── EVALUATION ────────────────────────────────────────────────────────────
    results: List[Dict] = []
    progress  = st.progress(0, text="Starting evaluation…")
    total     = len(uploaded_files)

    for i, f in enumerate(uploaded_files):
        progress.progress((i + 1) / total, text=f"Evaluating candidate {i+1} of {total}…")
        suffix = Path(f.name).suffix.lower()
        cand_name = Path(f.name).stem.replace("_", " ").replace("-", " ").title()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(f.read())
            tmp_path = tmp.name

        try:
            cv_text = _extract(tmp_path, suffix, extract_pdf_fn, extract_docx_fn)
            if not cv_text or len(cv_text.split()) < 5:
                raise ValueError("No readable text extracted from this file.")
            # Canonical evaluation via the shared engine; identity preserved.
            payload = run_match_fn(cv_text, job_text,
                                   candidate_name=cand_name,
                                   job_offer_id=selected_job_id)
            res     = payload["result"]
            expl    = payload["explanation"]
            sa      = expl.get("skill_analysis", {})
            hr      = expl.get("hiring_recommendation", {})
            pct     = res["percentage"]

            results.append({
                "Name":     cand_name,
                "Score":    pct,
                "Decision": hr.get("decision", decision_from_score(pct)),
                "Confidence": hr.get("confidence_level", ""),
                "Matched":  sa.get("matching_skills", []),
                "Critical": sa.get("critical_missing", []),
                "Summary":  hr.get("justification", ""),
            })
        except Exception as exc:
            results.append({
                "Name": Path(f.name).stem[:30], "Score": 0,
                "Decision": "ERROR", "Confidence": "", "Matched": [], "Critical": [],
                "Summary": str(exc),
            })
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    progress.empty()

    # ── SORT (deterministic: score desc, then name asc for ties) ───────────────
    results.sort(key=lambda r: (-r["Score"], r["Name"].lower()))

    # ── SUMMARY STATS ─────────────────────────────────────────────────────────
    valid   = [r for r in results if r["Decision"] != "ERROR"]
    n_hire  = sum(1 for r in valid if r["Decision"] == "HIRE")
    n_cons  = sum(1 for r in valid if r["Decision"] == "CONSIDER")
    n_rej   = sum(1 for r in valid if r["Decision"] == "REJECT")
    avg_scr = sum(r["Score"] for r in valid) / len(valid) if valid else 0
    top_scr = valid[0]["Score"] if valid else 0

    stat_row([
        {"icon_key": "users",       "value": str(total),        "label": "Candidates",     "variant": "brand"},
        {"icon_key": "check",       "value": str(n_hire),       "label": "Strong Fit",     "variant": "success"},
        {"icon_key": "alert",       "value": str(n_cons),       "label": "Potential Fit",  "variant": "warn"},
        {"icon_key": "x",           "value": str(n_rej),        "label": "Low Fit",        "variant": "danger"},
        {"icon_key": "activity",    "value": f"{avg_scr:.0f}%", "label": "Avg Score",      "variant": "brand"},
        {"icon_key": "award",       "value": f"{top_scr:.0f}%", "label": "Top Score",      "variant": "purple"},
    ])

    st.markdown("<br>", unsafe_allow_html=True)

    # ── CHART ─────────────────────────────────────────────────────────────────
    section_label("bar-chart", "SCORE DISTRIBUTION")
    chart_data = [{"Name": r["Name"], "Score": r["Score"]} for r in results]
    draw_ranking_chart(chart_data)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── LEADERBOARD CARDS ─────────────────────────────────────────────────────
    section_label("award", "CANDIDATE LEADERBOARD")
    for i, r in enumerate(results, 1):
        st.markdown(ranking_card(
            rank     = i,
            name     = r["Name"],
            score    = r["Score"],
            decision = r["Decision"],
            matched  = r["Matched"],
            critical = r["Critical"],
        ), unsafe_allow_html=True)

    # ── AI SUMMARY ────────────────────────────────────────────────────────────
    if valid:
        top = valid[0]
        st.markdown("<br>", unsafe_allow_html=True)
        section_label("brain", "AI EVALUATION SUMMARY")
        rec_dec = top["Decision"]
        card_cls = {"HIRE": "nh-insight-hire", "CONSIDER": "nh-insight-consider", "REJECT": "nh-insight-reject"}.get(rec_dec, "nh-insight-consider")
        st.markdown(f"""
        <div class="nh-insight {card_cls}">
          <div class="nh-insight-eyebrow">{ICONS['award']} &nbsp; TOP CANDIDATE · {top['Name'].upper()}</div>
          <div class="nh-insight-body">{top['Summary']}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── EXPORT ────────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    section_label("download", "EXPORT RESULTS")
    df_export = pd.DataFrame([{
        "Rank":        i + 1,
        "Candidate":   r["Name"],
        "Score (%)":   round(r["Score"], 1),
        "Decision":    r["Decision"],
        "Matched Skills": ", ".join(r["Matched"][:5]),
        "Priority Gaps":  ", ".join(r["Critical"][:3]),
    } for i, r in enumerate(results)])

    col_exp, col_down = st.columns([3, 1])
    with col_exp:
        with st.expander("View ranking table"):
            st.dataframe(df_export, width="stretch", hide_index=True)
    with col_down:
        st.download_button(
            label="Download CSV",
            data=df_export.to_csv(index=False),
            file_name="neuralhire_ranking.csv",
            mime="text/csv",
            key="csv_download",
        )
