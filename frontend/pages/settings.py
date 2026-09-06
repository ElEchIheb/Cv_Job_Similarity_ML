"""
frontend/pages/settings.py
NeuralHire — Platform Settings v4.0
No emojis. Recruiter language. Technical internals hidden.
SVG icons throughout.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict

import streamlit as st

from frontend.styles.theme import ICONS
from frontend.components.ui import (
    page_header, section_label, MODEL_LABELS,
)


def render(models: Dict, project_root: Path):
    page_header(
        badge="ENTERPRISE SETTINGS",
        title="Platform",
        highlight="Settings",
        subtitle=(
            "Configure decision thresholds, review AI system parameters, "
            "and manage platform preferences."
        ),
    )

    tab_thresholds, tab_models, tab_system, tab_about = st.tabs([
        "  Decision Thresholds  ",
        "  AI Models  ",
        "  System Status  ",
        "  About  ",
    ])

    # ── TAB 1: THRESHOLDS ─────────────────────────────────────────────────────
    with tab_thresholds:
        from frontend.decision_state import get_active_config, set_active_config
        from src.decisioning import DecisionConfigError

        active = get_active_config()
        st.markdown("<br>", unsafe_allow_html=True)
        section_label("settings", "DECISION THRESHOLDS")
        st.markdown(f"""
        <div class="nh-alert nh-alert-info" style="margin-bottom:18px;">
          <span class="nh-alert-icon">{ICONS['info']}</span>
          <span style="font-size:0.85rem;">
            These thresholds are the single source of truth for the Strong Fit /
            Potential Fit / Low Fit decision. Applying them affects every
            <strong>future</strong> evaluation in this session — Candidate Analysis,
            Talent Leaderboard and Bulk Evaluation alike. Previously saved
            evaluations keep the thresholds they were scored with. Settings are
            session-scoped and reset on logout.
          </span>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2, gap="large")
        with col1:
            hire_threshold = st.slider(
                "Strong Fit threshold (%)",
                min_value=50, max_value=95, value=int(active.strong_fit_threshold), step=1,
                help="Candidates at or above this score are recommended (HIRE).",
            )
            consider_threshold = st.slider(
                "Potential Fit threshold (%)",
                min_value=10, max_value=int(hire_threshold) - 1,
                value=min(int(active.potential_fit_threshold), int(hire_threshold) - 1), step=1,
                help="Scores between this value and the Strong Fit threshold are CONSIDER.",
            )
            if st.button("Apply thresholds", key="apply_thresholds", width="stretch"):
                try:
                    set_active_config(potential=float(consider_threshold),
                                      strong=float(hire_threshold))
                    st.success(
                        f"Active decision policy updated: Strong Fit ≥ {hire_threshold}%, "
                        f"Potential Fit {consider_threshold}–{hire_threshold - 1}%. "
                        "Future evaluations will use these thresholds."
                    )
                except DecisionConfigError as exc:
                    st.error(f"Invalid thresholds: {exc}")
            st.caption(
                f"Currently active: Strong Fit ≥ {int(active.strong_fit_threshold)}%, "
                f"Potential Fit ≥ {int(active.potential_fit_threshold)}%."
            )

        with col2:
            st.markdown(f"""
            <div class="nh-card">
              <div class="nh-section-label">THRESHOLD PREVIEW</div>
              <div style="margin-top:14px;">
                <div class="nh-arch-row" style="margin-bottom:6px;">
                  <div class="nh-arch-layer">Strong Fit</div>
                  <div class="nh-arch-tech">≥ {hire_threshold}%</div>
                  <div class="nh-arch-desc"><span class="nh-badge nh-badge-hire">Recommended</span></div>
                </div>
                <div class="nh-arch-row" style="margin-bottom:6px;">
                  <div class="nh-arch-layer">Potential Fit</div>
                  <div class="nh-arch-tech">{consider_threshold}% – {hire_threshold - 1}%</div>
                  <div class="nh-arch-desc"><span class="nh-badge nh-badge-consider">Consider</span></div>
                </div>
                <div class="nh-arch-row">
                  <div class="nh-arch-layer">Low Fit</div>
                  <div class="nh-arch-tech">Below {consider_threshold}%</div>
                  <div class="nh-arch-desc"><span class="nh-badge nh-badge-reject">Not Recommended</span></div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ── TAB 2: AI MODELS ──────────────────────────────────────────────────────
    with tab_models:
        st.markdown("<br>", unsafe_allow_html=True)
        section_label("brain", "LOADED AI MODELS")

        model_display = [
            {
                "key":       "hybrid",
                "label":     "Overall AI Match",
                "desc":      "Weighted ensemble combining all three evaluation methods for the most accurate and balanced compatibility score.",
                "strength":  "Highest accuracy. Robust. Explainable.",
                "icon":      "zap",
                "variant":   "amber",
                "color":     "var(--warn)",
            },
            {
                "key":       "embedding",
                "label":     "Semantic Relevance",
                "desc":      "Measures how closely the candidate's experience aligns with the role at a conceptual level, beyond simple keyword matching.",
                "strength":  "Captures meaning. Language-agnostic. Multilingual.",
                "icon":      "brain",
                "variant":   "purple",
                "color":     "var(--brand-2)",
            },
            {
                "key":       "tfidf",
                "label":     "Keyword Relevance",
                "desc":      "Analyses the statistical alignment of key terms and phrases between the candidate profile and the job requirements.",
                "strength":  "Fast. Precise on technical roles. Consistent.",
                "icon":      "search",
                "variant":   "brand",
                "color":     "var(--brand)",
            },
            {
                "key":       "skill",
                "label":     "Skills Assessment",
                "desc":      "Identifies and compares specific skills from the CV against required skills in the job posting using NLP extraction.",
                "strength":  "Skill-level precision. Domain-specific detection.",
                "icon":      "layers",
                "variant":   "cyan",
                "color":     "var(--success)",
            },
        ]

        for m in model_display:
            loaded = m["key"] in models
            status_html = (
                f'<span class="nh-badge nh-badge-hire" style="font-size:0.6rem;">Active</span>'
                if loaded else
                f'<span class="nh-badge nh-badge-reject" style="font-size:0.6rem;">Not Loaded</span>'
            )
            st.markdown(f"""
            <div class="nh-card" style="margin-bottom:10px;border-left:3px solid {m['color']};">
              <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap;">
                <div class="nh-feature-icon {m['variant']}" style="width:38px;height:38px;flex-shrink:0;">
                  {ICONS.get(m['icon'],'')}
                </div>
                <div style="flex:1;min-width:160px;">
                  <div style="display:flex;align-items:center;gap:10px;margin-bottom:5px;">
                    <span style="font-family:'Space Grotesk',sans-serif;font-size:1rem;font-weight:700;color:var(--text-primary)!important;">{m['label']}</span>
                    {status_html}
                  </div>
                  <div style="font-size:0.8rem;color:var(--text-muted)!important;line-height:1.65;margin-bottom:6px;">{m['desc']}</div>
                  <div style="font-size:0.7rem;color:{m['color']}!important;opacity:0.85;">{ICONS['check']} &nbsp;{m['strength']}</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ── TAB 3: SYSTEM STATUS ──────────────────────────────────────────────────
    with tab_system:
        st.markdown("<br>", unsafe_allow_html=True)
        section_label("cpu", "PLATFORM DIAGNOSTICS")

        # Python
        py_ver = sys.version.split()[0]
        st.markdown(f"""
        <div class="nh-card" style="margin-bottom:14px;">
          <div class="nh-section-label" style="margin-bottom:12px;">ENVIRONMENT</div>
          <div class="nh-arch-row" style="margin-bottom:6px;">
            <div class="nh-arch-layer">Python</div>
            <div class="nh-arch-tech">{py_ver}</div>
            <div class="nh-arch-desc">Runtime version</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Model status
        section_label("layers", "MODEL STATUS")
        for m_key, m_obj in models.items():
            label  = MODEL_LABELS.get(m_key, m_key.title())
            status = "Active" if m_obj is not None else "Unavailable"
            s_cls  = "nh-badge-hire" if status == "Active" else "nh-badge-reject"
            m_type = type(m_obj).__name__ if m_obj else "N/A"
            st.markdown(f"""
            <div class="nh-arch-row" style="margin-bottom:5px;">
              <div class="nh-arch-layer">{label}</div>
              <div class="nh-arch-tech" style="font-size:0.73rem;">{m_type}</div>
              <div class="nh-arch-desc"><span class="nh-badge {s_cls}" style="font-size:0.6rem;">{status}</span></div>
            </div>
            """, unsafe_allow_html=True)

        # Directory info (non-technical display)
        st.markdown("<br>", unsafe_allow_html=True)
        section_label("folder", "PLATFORM PATHS")
        st.markdown(f"""
        <div class="nh-arch-row" style="margin-bottom:5px;">
          <div class="nh-arch-layer">Project</div>
          <div class="nh-arch-tech" style="font-size:0.7rem;">{project_root}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── TAB 4: ABOUT ──────────────────────────────────────────────────────────
    with tab_about:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="nh-hero" style="padding:40px 36px;text-align:left;">
          <div style="display:flex;align-items:center;gap:14px;margin-bottom:22px;">
            <div class="nh-brand-icon" style="width:52px;height:52px;border-radius:15px;">{ICONS['zap']}</div>
            <div>
              <div style="font-family:'Space Grotesk',sans-serif;font-size:1.8rem;font-weight:700;
                          color:var(--text-primary)!important;letter-spacing:-0.05em;">Neural<span style="background:linear-gradient(135deg,var(--brand),var(--brand-2));-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Hire</span></div>
              <div style="font-size:0.65rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.18em;font-weight:700;margin-top:2px;">Enterprise Edition · v4.0</div>
            </div>
          </div>
          <div style="font-size:0.95rem;color:var(--text-secondary)!important;line-height:1.85;max-width:520px;">
            NeuralHire is an AI-powered recruitment evaluation platform designed to help HR professionals
            screen, compare, and rank candidates objectively and efficiently.<br><br>
            Built with three complementary evaluation engines — keyword analysis, semantic understanding,
            and skills detection — combined into a single explainable compatibility score.<br><br>
            <span style="color:var(--text-muted);font-size:0.8rem;">
            Final year engineering project (PFE) · AI Recruitment Intelligence
            </span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        section_label("layers", "TECHNOLOGY OVERVIEW")

        capabilities = [
            ("AI Matching",         "Three complementary algorithms — keyword, semantic, and skills-based"),
            ("Explainability",      "Gap analysis, competency profiling, and decision justification"),
            ("Multilingual",        "English and French CV/JD support out of the box"),
            ("Bulk Processing",     "Evaluate hundreds of candidates via spreadsheet upload"),
            ("Report Generation",   "Professional PDF reports with embedded charts and recommendations"),
            ("REST API",            "Full API access for integration with existing HR systems"),
        ]

        for cap, desc in capabilities:
            st.markdown(f"""
            <div class="nh-arch-row" style="margin-bottom:5px;">
              <div class="nh-arch-layer">{cap}</div>
              <div class="nh-arch-desc" style="margin-left:0;color:var(--text-secondary)!important;font-size:0.8rem;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
