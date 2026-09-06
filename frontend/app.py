"""
frontend/app.py
NeuralHire AI Platform — Enterprise Entry Point v4.0

============================================================================
DEPRECATED — superseded by the Next.js app in web/. Kept for reference only,
not maintained. Do not build new features here; all frontend work happens in
web/. This module is excluded from routine tests/CI.
============================================================================

Architecture:
  Single-page app with custom sidebar navigation.
  NO multi-page Streamlit auto-detection (pages/ is a package, not a MPA dir).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Dict
from src.config import settings
from src.database import SessionLocal
from src import models_db

# ── Path setup — must be first ─────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib
matplotlib.use("Agg")

import streamlit as st

# ── Page config — FIRST st call ─────────────────────────────────────────────
st.set_page_config(
    page_title="NeuralHire — AI Recruitment Platform",
    page_icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><polygon points='13 2 3 14 12 14 11 22 21 10 12 10 13 2' fill='%2300BFFF'/></svg>",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help":     None,
        "Report a bug": None,
        "About":        "NeuralHire v4.0 — AI-powered recruitment evaluation.",
    },
)

# ── Design system injection ────────────────────────────────────────────────
from frontend.styles.theme import build_css, ICONS
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
st.markdown(build_css(st.session_state.theme), unsafe_allow_html=True)

# ── Backend imports ────────────────────────────────────────────────────────
from src.explainability.explainer import MatchingExplainer, RecommendationEngine
from src.fusion.hybrid_scorer import HybridMatcher
from src.models.embedding_model import EmbeddingMatcher
from src.models.skill_matcher import SkillMatcher
from src.models.tfidf_model import TFIDFMatcher
from src.parsing.parser import extract_text_from_pdf, extract_text_from_docx

try:
    from src.reporting.pdf_generator import MatchReportPDF
    _PDF_AVAILABLE = True
except Exception:
    _PDF_AVAILABLE = False
    MatchReportPDF = None

# ── Authentication Check ───────────────────────────────────────────────────
import requests

API_BASE_URL = "http://localhost:8000/api/v1"

def check_auth():
    # Attempt to recover from cookies if technically supported (Streamlit >= 1.39)
    if "access_token" not in st.session_state:
        if hasattr(st, "context") and hasattr(st.context, "cookies"):
            token = st.context.cookies.get("access_token")
            if token:
                st.session_state.access_token = token

    if "access_token" not in st.session_state:
        return False
        
    if "user_id" not in st.session_state:
        try:
            response = requests.get(
                f"{API_BASE_URL}/auth/me", 
                headers={"Authorization": f"Bearer {st.session_state.access_token}"}
            )
            if response.status_code == 200:
                data = response.json()
                st.session_state.user_id = data["id"]
                st.session_state.user_full_name = data["full_name"]
                st.session_state.user_role = data["role"]
                return True
            else:
                del st.session_state["access_token"]
                return False
        except Exception:
            return False
            
    return True

if not check_auth():
    from frontend.pages import auth
    auth.render()
    st.stop()

if "just_logged_out" in st.session_state:
    st.components.v1.html(
        '<script>document.cookie = "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";</script>',
        height=0, width=0
    )
    del st.session_state["just_logged_out"]

# Set cookie if just logged in
if "just_logged_in" in st.session_state:
    token = st.session_state.just_logged_in
    st.components.v1.html(
        f'<script>document.cookie = "access_token={token}; path=/; max-age=86400";</script>',
        height=0, width=0
    )
    del st.session_state["just_logged_in"]

# ── Page imports ───────────────────────────────────────────────────────────
from frontend.pages import (
    dashboard, single_match, ranking,
    model_comparison,
    evaluation_metrics, settings,
    candidate_history, job_offers, analysis_history
)


# ══════════════════════════════════════════════════════════════════════════
# AI MODEL LOADING
# ══════════════════════════════════════════════════════════════════════════

@st.cache_resource(show_spinner="Loading AI models — this takes a moment on first run…")
def _load_models() -> Dict:
    from src.models.model_loader import load_production_models
    return load_production_models()


@st.cache_resource(show_spinner=False)
def _run_db_maintenance() -> Dict:
    """Ensure schema + backfill legacy decisions once per process."""
    from src.database import engine
    from src.db_maintenance import run_maintenance
    return run_maintenance(engine)


_run_db_maintenance()
MODELS      = _load_models()
HYBRID      = MODELS["hybrid"]
EXPLAINER   = MODELS["explainer"]
RECOMMENDER = MODELS["recommender"]


# ══════════════════════════════════════════════════════════════════════════
# CORE MATCHING FUNCTION
# ══════════════════════════════════════════════════════════════════════════

def run_match(cv_text: str, job_text: str, model: str = "hybrid",
              candidate_name: str = None, candidate_email: str = None,
              job_offer_id: int = None, persist: bool = True) -> Dict:
    """Run a CV–Job evaluation through the canonical matching service.

    Decision, confidence, thresholds and metadata all come from the single
    DecisionEngine via src.matching.service, and are persisted with de-duplicated
    Candidate/Job entities. Returns {result, explanation, recommendations, ...}.
    """
    from src.matching.service import evaluate_and_persist
    from frontend.decision_state import get_active_config

    config       = get_active_config()
    recruiter_id = st.session_state.get("user_id")
    db = SessionLocal()
    try:
        payload = evaluate_and_persist(
            db, MODELS, cv_text, job_text,
            model_key=model,
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            job_offer_id=job_offer_id,
            recruiter_id=recruiter_id,
            config=config,
            persist=persist,
        )
    finally:
        db.close()
    return payload


# ══════════════════════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION
# Keys used for routing — no emojis, no technical jargon
# ══════════════════════════════════════════════════════════════════════════

# Initialize current route state if not set
if "current_route" not in st.session_state:
    st.session_state.current_route = "dashboard"

# Navigation items: (display label, route key, icon descriptor)
_NAV = [
    ("Overview",                  "dashboard",    ":material/dashboard:"),
    ("Candidate History",         "candidates",   ":material/group:"),
    ("Job Offers",                "jobs",         ":material/work:"),
    ("Analysis History",          "history",      ":material/history:"),
    ("Candidate Analysis",        "single_match", ":material/person_search:"),
    ("Talent Leaderboard",        "ranking",      ":material/leaderboard:"),
    ("AI Insights",               "comparison",   ":material/psychology:"),
    ("AI Quality Center",         "metrics",      ":material/analytics:"),
    ("Settings",                  "settings",     ":material/settings:"),
]

with st.sidebar:
    # ── Brand ──────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="nh-brand">
      <div class="nh-brand-row">
        <div class="nh-brand-icon">{ICONS['zap']}</div>
        <div>
          <div class="nh-brand-text-name">Neural<span class="accent">Hire</span></div>
          <div class="nh-brand-text-sub">AI Recruitment Platform</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Nav section label ──────────────────────────────────────────────────
    st.markdown('<div class="nh-nav-section-label">NAVIGATION</div>', unsafe_allow_html=True)

    # ── Enterprise Button Navigation — 0 Raw SVG text ──────────────────────
    for label, route_key, icon_str in _NAV:
        is_active = (st.session_state.current_route == route_key)
        btn_kind  = "primary" if is_active else "secondary"
        if st.button(
            label,
            key=f"nav_item_{route_key}",
            icon=icon_str,
            type=btn_kind,
            width="stretch",
        ):
            if st.session_state.current_route != route_key:
                st.session_state.current_route = route_key
                st.rerun()

    current_route = st.session_state.current_route

    # ── Appearance, Status & Logout ────────────────────────────────────────
    st.markdown("<hr style='margin: 0.9rem 0;'>", unsafe_allow_html=True)

    _is_dark = st.session_state.theme == "dark"
    _toggle_label = "Light mode" if _is_dark else "Dark mode"
    _toggle_icon  = ":material/light_mode:" if _is_dark else ":material/dark_mode:"
    if st.button(_toggle_label, key="btn_theme_toggle", icon=_toggle_icon,
                 width="stretch"):
        st.session_state.theme = "light" if _is_dark else "dark"
        st.rerun()

    if st.button("Logout", key="btn_logout", icon=":material/logout:", width="stretch"):
        for key in ["access_token", "user_id", "user_full_name", "user_role", "auth_view"]:
            if key in st.session_state:
                del st.session_state[key]
        # Erase cookie on logout
        st.session_state.just_logged_out = True
        st.rerun()

    st.markdown("""
    <div class="nh-sidebar-footer">
      <div class="nh-sidebar-status-badge">
        <div class="nh-status-dot"></div>
        <div class="nh-status-label">All systems online</div>
      </div>
      <div class="nh-sidebar-version">NeuralHire v4.0 · Enterprise</div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# PAGE ROUTING
# ══════════════════════════════════════════════════════════════════════════

# ── Executive Top Bar ──────────────────────────────────────────────────
current_page_label = next((label for label, route, _ in _NAV if route == current_route), "NeuralHire")
user_name = st.session_state.get("user_full_name", "HR")
initials = "".join([n[0] for n in user_name.split() if n]).upper()[:2] if user_name else "HR"

st.markdown(f"""
<div class="nh-topbar">
  <div class="nh-topbar-left">
    <div class="nh-topbar-breadcrumb">
      <span class="root">NeuralHire</span>
      <span class="sep">/</span>
      <span class="current">{current_page_label}</span>
    </div>
  </div>
  <div class="nh-topbar-center">
    <div class="nh-topbar-search">
      {ICONS['search']}
      <input type="text" placeholder="Search candidates, positions, skill keywords..." disabled />
    </div>
  </div>
  <div class="nh-topbar-right">
    <div class="nh-topbar-status">
      <div class="nh-status-dot"></div>
      <span>All Systems Operational</span>
    </div>
    <div class="nh-topbar-avatar" title="{user_name}">{initials}</div>
  </div>
</div>
""", unsafe_allow_html=True)

if current_route == "dashboard":
    dashboard.render()

elif current_route == "candidates":
    candidate_history.render()

elif current_route == "jobs":
    job_offers.render()

elif current_route == "history":
    analysis_history.render()

elif current_route == "single_match":
    single_match.render(
        run_match_fn    = run_match,
        extract_pdf_fn  = extract_text_from_pdf,
        extract_docx_fn = extract_text_from_docx,
        pdf_available   = _PDF_AVAILABLE,
        MatchReportPDF  = MatchReportPDF,
    )

elif current_route == "ranking":
    ranking.render(
        run_match_fn    = run_match,
        extract_pdf_fn  = extract_text_from_pdf,
        extract_docx_fn = extract_text_from_docx,
    )

elif current_route == "comparison":
    model_comparison.render(run_match_fn=run_match)

elif current_route == "metrics":
    evaluation_metrics.render(project_root=PROJECT_ROOT)

elif current_route == "settings":
    settings.render(models=MODELS, project_root=PROJECT_ROOT)
