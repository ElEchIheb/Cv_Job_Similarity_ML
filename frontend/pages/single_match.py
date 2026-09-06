"""
frontend/pages/single_match.py
NeuralHire — Candidate Analysis Page v4.0
No emojis. Recruiter language. SVG icons.
"""
from __future__ import annotations

import tempfile
import time
from pathlib import Path
from typing import Dict

import streamlit as st

from frontend.styles.theme import ICONS
from frontend.components.ui import (
    page_header, section_label, score_hero,
    draw_radar, draw_component_bars,
    skill_section, ai_recommendation_panel,
    swot_section, recommendations_section,
)

_DEFAULT_CV = (
    "PROFILE\n"
    "Senior ML Engineer with 6 years of experience building production AI systems.\n\n"
    "SKILLS\n"
    "Python, PyTorch, TensorFlow, MLflow, Docker, Kubernetes, FastAPI, PostgreSQL, "
    "AWS, CI/CD, strong communication and teamwork skills.\n\n"
    "EXPERIENCE\n"
    "2018–2024: ML Engineer at TechCorp\n"
    "Built and maintained production ML pipelines serving 10M users daily.\n"
    "Led a team of 4 engineers. Designed the feature store and model registry.\n\n"
    "EDUCATION\n"
    "MSc Computer Science — University of Paris"
)

_DEFAULT_JD = (
    "We are looking for a Senior ML Engineer to join our AI team.\n\n"
    "REQUIRED SKILLS:\n"
    "Python, PyTorch or TensorFlow, MLflow (mandatory), Docker, Kubernetes (mandatory), "
    "FastAPI, PostgreSQL, AWS or GCP.\n\n"
    "RESPONSIBILITIES:\n"
    "Design and deploy ML models at scale. Build robust pipelines. Mentor junior engineers.\n\n"
    "REQUIREMENTS:\n"
    "5+ years of experience. Master's degree in Computer Science or related field."
)

# AI model display names (recruiter-facing)
_MODEL_OPTIONS = {
    "hybrid":    "Overall AI Match — Recommended",
    "embedding": "Semantic Relevance only",
    "tfidf":     "Keyword Relevance only",
    "skill":     "Skills Assessment only",
}


def _display_result(payload: Dict, candidate_name: str, job_title: str,
                    pdf_available: bool, MatchReportPDF=None):
    result      = payload["result"]
    explanation = payload["explanation"]
    recommendations = payload["recommendations"]
    pct         = result["percentage"]
    hiring_rec  = explanation.get("hiring_recommendation", {})
    comp_scores = result.get("component_scores", {})

    st.markdown('<div class="nh-result">', unsafe_allow_html=True)

    # ── Row 1: Score Ring + Radar ─────────────────────────────────────────────
    col_score, col_radar = st.columns([2, 3], gap="large")

    with col_score:
        st.markdown('<div class="nh-card" style="height:100%;">', unsafe_allow_html=True)
        score_hero(pct)
        if comp_scores:
            st.markdown("<br>", unsafe_allow_html=True)
            section_label("layers", "SCORE BREAKDOWN")
            draw_component_bars(comp_scores)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_radar:
        st.markdown('<div class="nh-card" style="height:100%;">', unsafe_allow_html=True)
        section_label("radar", "COMPETENCY PROFILE")

        verdict = explanation.get("verdict", "")
        if verdict:
            st.markdown(f"""
            <div style="font-size:0.82rem;color:var(--text-secondary);margin-bottom:12px;
                        padding:10px 14px;background:var(--brand-bg);
                        border:1px solid var(--border);border-radius:8px;line-height:1.65;">
              {verdict}
            </div>
            """, unsafe_allow_html=True)
        draw_radar(explanation.get("radar_data", {}))
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── AI Insight Panel ──────────────────────────────────────────────────────
    ai_recommendation_panel(hiring_rec, pct)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Analysis Tabs ─────────────────────────────────────────────────────────
    tab_skills, tab_gaps, tab_actions, tab_raw = st.tabs([
        "  Skills Match  ",
        "  Strengths & Gaps  ",
        "  Recommended Actions  ",
        "  Raw Data  ",
    ])

    with tab_skills:
        st.markdown("<br>", unsafe_allow_html=True)
        skill_section(explanation.get("skill_analysis", {}))

        sem = explanation.get("semantic_analysis", {})
        if sem:
            st.markdown("<br>", unsafe_allow_html=True)
            section_label("brain", "SEMANTIC ANALYSIS")
            s1, s2, s3 = st.columns(3)
            s1.metric("Semantic Match",   f"{sem.get('score', 0):.1f}%")
            s2.metric("Topic Overlap",    f"{sem.get('theme_overlap', 0)*100:.0f}%")
            s3.metric("Interpretation",   sem.get("interpretation", "N/A"))

    with tab_gaps:
        st.markdown("<br>", unsafe_allow_html=True)
        swot_section(explanation.get("gap_analysis", {}), explanation.get("experience_fit", {}))

    with tab_actions:
        st.markdown("<br>", unsafe_allow_html=True)
        recommendations_section(recommendations)

    with tab_raw:
        st.markdown("<br>", unsafe_allow_html=True)
        section_label("search", "EVALUATION DATA")
        # Hide raw JSON from default view — put it in expander
        with st.expander("View raw evaluation payload"):
            st.json(payload)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── PDF Export ────────────────────────────────────────────────────────────
    if pdf_available and MatchReportPDF is not None:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("---")
        section_label("file-text", "EXPORT EVALUATION REPORT")
        st.markdown(f"""
        <div class="nh-card" style="padding:18px 22px;display:flex;align-items:center;gap:18px;flex-wrap:wrap;">
          <div style="color:var(--neon-cyan);">{ICONS['file-text']}</div>
          <div style="flex:1;min-width:180px;">
            <div style="font-size:0.94rem;font-weight:700;color:var(--text-primary)!important;margin-bottom:3px;font-family:'Space Grotesk',sans-serif;">
              Professional PDF Report
            </div>
            <div style="font-size:0.78rem;color:var(--text-muted)!important;line-height:1.65;">
              Branded, printable report with embedded charts, skills matrix,
              and personalised interview recommendations.
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Generate PDF Report", key="pdf_export_btn"):
            with st.spinner("Generating PDF report…"):
                try:
                    generator = MatchReportPDF()
                    pdf_bytes = generator.generate(
                        result=result, explanation=explanation,
                        recommendations=recommendations,
                        candidate_name=candidate_name or "Candidate",
                        job_title=job_title or "Position",
                    )
                    fname = f"NeuralHire_{(candidate_name or 'report').replace(' ', '_')}.pdf"
                    st.download_button(
                        label="Download PDF Report",
                        data=pdf_bytes, file_name=fname,
                        mime="application/pdf", key="pdf_download_btn",
                    )
                    st.success("Report generated successfully.")
                except Exception as exc:
                    st.error(f"Report generation failed: {exc}")
    else:
        st.info("PDF export requires the reportlab package.")


def render(run_match_fn, extract_pdf_fn, extract_docx_fn,
           pdf_available: bool, MatchReportPDF=None):
    page_header(
        badge="CANDIDATE EVALUATION",
        title="Candidate",
        highlight="Analysis",
        subtitle=(
            "Evaluate a candidate's profile against a job description using the "
            "NeuralHire AI engine — receive a compatibility score, skill breakdown, "
            "and a clear hire recommendation."
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

    # ── Configuration ─────────────────────────────────────────────────────────
    with st.expander("Candidate & Position Details", expanded=True):
        jcol, mcol = st.columns([3, 2])
        with jcol:
            selected_job_id = st.selectbox(
                "Select Job Offer *",
                options=[None] + list(job_options.keys()),
                format_func=lambda x: job_options[x] if x else "— Select a Job Offer —"
            )
        with mcol:
            model_choice = st.selectbox(
                "Evaluation Method",
                list(_MODEL_OPTIONS.keys()),
                format_func=lambda x: _MODEL_OPTIONS[x],
            )
            
        c1, c2 = st.columns(2)
        with c1:
            candidate_name = st.text_input("Candidate Name", placeholder="e.g. Alice Martin")
        with c2:
            candidate_email = st.text_input("Candidate Email", placeholder="e.g. alice@example.com")

        input_mode = st.radio(
            "CV Source",
            ["Paste Text", "Upload File (PDF or DOCX)"],
            horizontal=True,
        )

    # ── Input Panels ──────────────────────────────────────────────────────────
    col_cv, col_jd = st.columns(2, gap="large")
    cv_text  = ""
    job_text = ""

    with col_cv:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
          <div style="width:7px;height:7px;border-radius:50%;background:var(--brand);box-shadow:0 0 7px var(--brand);"></div>
          <span style="font-size:0.66rem;font-weight:700;color:var(--text-muted);letter-spacing:.14em;text-transform:uppercase;">CANDIDATE CV</span>
        </div>
        """, unsafe_allow_html=True)

        if input_mode == "Paste Text":
            cv_text = st.text_area(
                "CV", height=300,
                placeholder="Paste the candidate's CV here — include skills, experience, and education.",
                label_visibility="collapsed",
                value=_DEFAULT_CV,
            )
        else:
            # Premium upload zone
            st.markdown(f"""
            <div style="text-align:center;padding:8px 0 6px;color:var(--text-muted);font-size:0.78rem;">
              {ICONS['upload']} &nbsp; Drag and drop or click to upload
            </div>
            """, unsafe_allow_html=True)
            uploaded_cv = st.file_uploader(
                "Upload CV", type=["pdf", "docx"], label_visibility="collapsed"
            )
            if uploaded_cv:
                with st.spinner("Extracting text from file…"):
                    suffix = Path(uploaded_cv.name).suffix.lower()
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(uploaded_cv.read())
                        tmp_path = tmp.name
                    try:
                        cv_text = (extract_pdf_fn(tmp_path) if suffix == ".pdf"
                                   else extract_docx_fn(tmp_path))
                        Path(tmp_path).unlink(missing_ok=True)
                        st.success(f"Extracted {len(cv_text.split())} words")
                        with st.expander("Preview extracted text"):
                            st.text(cv_text[:700] + ("…" if len(cv_text) > 700 else ""))
                    except Exception as e:
                        st.error(f"Could not read file: {e}")

    with col_jd:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
          <div style="width:7px;height:7px;border-radius:50%;background:var(--brand-2);box-shadow:0 0 7px var(--brand-2);"></div>
          <span style="font-size:0.66rem;font-weight:700;color:var(--text-muted);letter-spacing:.14em;text-transform:uppercase;">JOB DESCRIPTION</span>
        </div>
        """, unsafe_allow_html=True)
        
        job_text = ""
        job_title = "Selected Job"
        if selected_job_id:
            db = SessionLocal()
            try:
                job = db.query(models_db.JobOffer).filter(models_db.JobOffer.id == selected_job_id).first()
                if job:
                    job_text = f"{job.title}\n\n{job.description}\n\nRequired Skills: {job.required_skills_raw}"
                    job_title = job.title
            finally:
                db.close()
                
        st.text_area(
            "JD", height=300,
            placeholder="Select a Job Offer above to view its description.",
            label_visibility="collapsed",
            value=job_text,
            disabled=True,
        )

    # ── Analyse Button ────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    _, btn_col, _ = st.columns([1, 2, 1])
    with btn_col:
        analyse = st.button("Run Evaluation", width="stretch", key="analyse_btn")

    if analyse:
        if not selected_job_id:
            st.error("Please select a Job Offer.")
        elif not cv_text.strip():
            st.error("Please provide a CV.")
        elif len(cv_text.split()) < 5:
            st.warning("Please provide more detailed CV text (minimum 5 words).")
        else:
            with st.spinner("Running AI evaluation…"):
                t0 = time.time()
                try:
                    payload = run_match_fn(
                        cv_text, job_text, model=model_choice,
                        candidate_name=candidate_name,
                        candidate_email=candidate_email,
                        job_offer_id=selected_job_id
                    )
                    elapsed = time.time() - t0
                    pct     = payload["result"]["percentage"]
                    st.markdown(f"""
                    <div class="nh-alert nh-alert-success" style="margin:14px 0;">
                      <span class="nh-alert-icon">{ICONS['check']}</span>
                      <span>Evaluation complete in <strong>{elapsed:.2f}s</strong>
                      — Compatibility score: <strong>{pct:.1f}%</strong></span>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown("---")
                    _display_result(payload, candidate_name, job_title, pdf_available, MatchReportPDF)
                except Exception as exc:
                    st.error(f"Evaluation failed: {exc}")
                    st.exception(exc)
