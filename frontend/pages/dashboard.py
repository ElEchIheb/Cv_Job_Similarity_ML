"""
frontend/pages/dashboard.py
NeuralHire — Overview Dashboard v4.0
No emojis. Recruiter language. SVG icons only.
"""
from __future__ import annotations
import streamlit as st
from frontend.styles.theme import ICONS
from frontend.components.ui import (
    page_header, section_label, stat_row,
    feature_card, architecture_table,
)


def render():
    # ── HERO ─────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="nh-hero">
      <div class="nh-hero-eyebrow">
        <div class="nh-status-dot" style="width:5px;height:5px;"></div>
        AI-POWERED RECRUITMENT INTELLIGENCE
      </div>
      <div class="nh-hero-title">
        Evaluate smarter.<br>
        <span class="glow">Hire with confidence.</span>
      </div>
      <div class="nh-hero-sub">
        NeuralHire combines deep semantic understanding, multi-dimensional skill analysis,
        and instant gap profiling to deliver objective, actionable candidate decisions.
      </div>
    </div>
    """, unsafe_allow_html=True)

    from src.database import SessionLocal
    from src import models_db
    from sqlalchemy import func

    db = SessionLocal()
    try:
        total_candidates = db.query(models_db.Candidate).count()
        total_jobs = db.query(models_db.JobOffer).count()
        total_matches = db.query(models_db.MatchResult).count()
        avg_score = db.query(func.avg(models_db.MatchResult.final_score)).scalar() or 0
        hire_count = db.query(models_db.MatchResult).filter(models_db.MatchResult.decision == "HIRE").count()
        hire_pct = (hire_count / total_matches * 100) if total_matches > 0 else 0
    finally:
        db.close()

    # ── HERO STATS ────────────────────────────────────────────────────────────
    stat_row([
        {"icon_key": "users",      "value": f"{total_candidates:,}", "label": "Candidates Evaluated","variant": "brand"},
        {"icon_key": "award",      "value": f"{avg_score*100:.1f}%" if avg_score <= 1.0 else f"{avg_score:.1f}%",   "label": "Avg. Compatibility", "variant": "success"},
        {"icon_key": "shield",     "value": f"{hire_pct:.1f}%", "label": "HIRE Rate",     "variant": "purple"},
        {"icon_key": "zap",        "value": f"{total_jobs:,}", "label": "Active Job Offers",  "variant": "warn"},
        {"icon_key": "file-text",  "value": f"{total_matches:,}",  "label": "Total Match Reports", "variant": "brand"},
    ])

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ── AI PIPELINE ───────────────────────────────────────────────────────────
    section_label("activity", "EVALUATION PIPELINE")
    st.markdown(f"""
    <div class="nh-card" style="padding: 22px 30px;">
      <div class="nh-pipeline">
        <div class="nh-pipeline-step">
          <div class="nh-pipeline-icon">{ICONS['file-text']}</div>
          <div class="nh-pipeline-label">Parse</div>
          <div class="nh-pipeline-desc">CV &amp; JD<br>text extraction</div>
        </div>
        <div class="nh-pipeline-step">
          <div class="nh-pipeline-icon">{ICONS['search']}</div>
          <div class="nh-pipeline-label">Identify</div>
          <div class="nh-pipeline-desc">Skills &amp; keyword<br>detection</div>
        </div>
        <div class="nh-pipeline-step">
          <div class="nh-pipeline-icon">{ICONS['brain']}</div>
          <div class="nh-pipeline-label">Evaluate</div>
          <div class="nh-pipeline-desc">AI compatibility<br>scoring</div>
        </div>
        <div class="nh-pipeline-step">
          <div class="nh-pipeline-icon">{ICONS['radar']}</div>
          <div class="nh-pipeline-label">Explain</div>
          <div class="nh-pipeline-desc">Gap analysis<br>&amp; profiling</div>
        </div>
        <div class="nh-pipeline-step">
          <div class="nh-pipeline-icon">{ICONS['file-text']}</div>
          <div class="nh-pipeline-label">Report</div>
          <div class="nh-pipeline-desc">PDF export<br>&amp; decision</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ── FEATURE CARDS ─────────────────────────────────────────────────────────
    section_label("grid", "PLATFORM FEATURES")

    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        st.markdown(feature_card(
            "brain", "blue",
            "Hybrid AI Scoring",
            "Three complementary AI methods — keyword relevance, semantic understanding, "
            "and skills assessment — combined into a single, balanced compatibility score."
        ), unsafe_allow_html=True)
    with c2:
        st.markdown(feature_card(
            "radar", "purple",
            "Explainable Results",
            "Every score includes a competency profile, skill gap breakdown, and a clear "
            "Hire / Consider / Reject recommendation with full justification."
        ), unsafe_allow_html=True)
    with c3:
        st.markdown(feature_card(
            "file-text", "cyan",
            "Professional Reports",
            "Export branded, printable evaluation reports with embedded charts, "
            "skills matrix, decision support, and interview recommendations."
        ), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    c4, c5, c6 = st.columns(3, gap="medium")
    with c4:
        st.markdown(feature_card(
            "award", "amber",
            "Talent Ranking",
            "Upload multiple CVs and automatically rank every candidate by fit score. "
            "Export the leaderboard as a CSV for direct reporting."
        ), unsafe_allow_html=True)
    with c5:
        st.markdown(feature_card(
            "folder", "violet",
            "Bulk Evaluation",
            "Upload a spreadsheet of CV–job pairs and run the full AI pipeline in one click. "
            "Built for high-volume recruitment campaigns."
        ), unsafe_allow_html=True)
    with c6:
        st.markdown(feature_card(
            "trending-up", "rose",
            "Performance Metrics",
            "Scientific benchmarking with accuracy scores, F1 metrics, and comparison "
            "charts across all evaluation dimensions."
        ), unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ── TECH STACK + QUICK START ──────────────────────────────────────────────
    col_arch, col_guide = st.columns([3, 2], gap="large")

    with col_arch:
        section_label("cpu", "TECHNOLOGY OVERVIEW")
        architecture_table()

    with col_guide:
        section_label("chevron-right", "GETTING STARTED")
        steps = [
            ("target",      "Candidate Analysis",  "Paste a CV and job description for instant AI evaluation with full skill breakdown."),
            ("users",       "Talent Ranking",       "Upload multiple CVs and rank all candidates for a position automatically."),
            ("folder",      "Bulk Evaluation",      "Upload a spreadsheet to evaluate hundreds of candidate pairs simultaneously."),
            ("bar-chart",   "Model Comparison",     "Compare all four evaluation methods side-by-side on the same input."),
        ]
        for icon_key, title, desc in steps:
            st.markdown(f"""
            <div class="nh-arch-row" style="align-items:flex-start; padding:12px 14px; margin-bottom:5px;">
              <div style="color:var(--neon-blue);flex-shrink:0;margin-top:2px;">{ICONS[icon_key]}</div>
              <div>
                <div style="font-size:0.86rem;font-weight:700;color:var(--text-primary)!important;margin-bottom:3px;font-family:'Space Grotesk',sans-serif;">{title}</div>
                <div style="font-size:0.74rem;color:var(--text-muted)!important;line-height:1.6;">{desc}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ── FOOTER ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="nh-footer">
      NeuralHire AI Platform v4.0 &nbsp;&middot;&nbsp;
      Enterprise Recruitment Intelligence &nbsp;&middot;&nbsp;
      Powered by AI
    </div>
    """, unsafe_allow_html=True)
