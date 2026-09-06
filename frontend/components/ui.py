"""
frontend/components/ui.py
NeuralHire — Enterprise UI Components v4.0

All emojis removed. All technical jargon hidden behind recruiter-friendly language.
SVG icons from the ICONS dict in theme.py used throughout.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import streamlit as st

from frontend.styles.theme import ICONS, chart_palette


def _theme() -> str:
    """Current UI theme from session state ('dark' by default)."""
    try:
        return st.session_state.get("theme", "dark")
    except Exception:
        return "dark"


def _palette() -> dict:
    return chart_palette(_theme())


# ─────────────────────────────────────────────────────────────────────────────
# BUSINESS LANGUAGE MAP  (Issue 3 — hide technical jargon)
# ─────────────────────────────────────────────────────────────────────────────

# Model names → recruiter-friendly labels
MODEL_LABELS = {
    "hybrid":    "Overall AI Match",
    "embedding": "Semantic Relevance",
    "tfidf":     "Keyword Relevance",
    "skill":     "Skills Assessment",
    "HYBRID":    "Overall AI Match",
    "EMBEDDING": "Semantic Relevance",
    "TFIDF":     "Keyword Relevance",
    "SKILL":     "Skills Assessment",
}

# Technical score keys → human labels
SCORE_LABELS = {
    "hybrid_score":    "Overall AI Match",
    "embedding_score": "Semantic Relevance",
    "tfidf_score":     "Keyword Relevance",
    "skill_score":     "Skills Assessment",
}

MODEL_DESCRIPTIONS = {
    "TFIDF":     "Analyses keyword alignment between the candidate's profile and job requirements.",
    "EMBEDDING": "Measures how closely the candidate's experience matches the role at a conceptual level.",
    "SKILL":     "Compares detected skills from the CV against the required skills in the job posting.",
    "HYBRID":    "Combines all evaluation dimensions into a single, balanced compatibility score.",
}

MODEL_ICONS = {
    "TFIDF":     "search",
    "EMBEDDING": "brain",
    "SKILL":     "layers",
    "HYBRID":    "zap",
}

MODEL_COLORS = {
    "TFIDF":     "#6366F1",
    "EMBEDDING": "#8B5CF6",
    "SKILL":     "#06B6D4",
    "HYBRID":    "#F59E0B",
}

MODEL_ICON_VARIANTS = {
    "TFIDF":     "brand",
    "EMBEDDING": "purple",
    "SKILL":     "cyan",
    "HYBRID":    "amber",
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def _active_engine():
    """DecisionEngine bound to the current session's active configuration."""
    from src.decisioning import DecisionEngine
    from frontend.decision_state import get_active_config
    return DecisionEngine(get_active_config())


def score_color(pct: float) -> str:
    p = _palette()
    decision = _active_engine().classify(pct)
    return {"HIRE": p["success"], "CONSIDER": p["warn"], "REJECT": p["danger"]}[decision]


def decision_from_score(pct: float) -> str:
    """Canonical decision for a score — delegates to the central DecisionEngine."""
    return _active_engine().classify(pct)


def badge_class(decision: str) -> str:
    return {"HIRE": "nh-badge-hire", "CONSIDER": "nh-badge-consider", "REJECT": "nh-badge-reject"}.get(decision, "nh-badge-consider")


def badge_icon(decision: str) -> str:
    m = {"HIRE": ICONS["check"], "CONSIDER": ICONS["alert"], "REJECT": ICONS["x"]}
    return m.get(decision, ICONS["alert"])


def score_class(pct: float) -> str:
    return {"HIRE": "hire", "CONSIDER": "consider", "REJECT": "reject"}[_active_engine().classify(pct)]


def _avatar_bg(name: str) -> tuple:
    colors = [
        ("rgba(99,102,241,0.14)",  "#6366F1"),
        ("rgba(139,92,246,0.14)",  "#8B5CF6"),
        ("rgba(6,182,212,0.14)",   "#0891B2"),
        ("rgba(16,185,129,0.14)",  "#059669"),
        ("rgba(245,158,11,0.14)",  "#B45309"),
    ]
    return colors[sum(ord(c) for c in name) % len(colors)]


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR COMPONENTS
# ─────────────────────────────────────────────────────────────────────────────

def sidebar_brand():
    """Legacy compat — brand is now in app.py directly."""
    pass


def sidebar_status(models_ready: bool = True):
    """Legacy compat — status is now in app.py directly."""
    pass


def sidebar_footer():
    """Legacy compat — footer is now in app.py directly."""
    pass


# ─────────────────────────────────────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────────────────────────────────────

def page_header(badge: str, title: str, highlight: str, subtitle: str):
    """Cinematic page header with animated badge and gradient title."""
    st.markdown(f"""
    <div class="nh-page-header">
      <div class="nh-page-badge">
        <div class="nh-page-badge-dot"></div>
        {badge}
      </div>
      <div class="nh-page-title">{title} <span class="grad">{highlight}</span></div>
      <div class="nh-page-subtitle">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


def section_label(icon_key: str, text: str):
    """Section label with SVG icon."""
    icon_html = ICONS.get(icon_key, "")
    st.markdown(f"""
    <div class="nh-section-label">
      <span class="icon">{icon_html}</span>
      {text}
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# STAT CARDS
# ─────────────────────────────────────────────────────────────────────────────

def stat_row(stats: List[Dict]):
    """
    Premium stat card row.
    Each dict: {icon_key, value, label, variant}
    variant: '' | 'success' | 'warn' | 'danger' | 'brand' | 'purple'
    """
    cols = st.columns(len(stats))
    for col, s in zip(cols, stats):
        variant  = s.get("variant", "brand")
        icon_key = s.get("icon_key", "activity")
        icon_html = ICONS.get(icon_key, "")
        val_cls  = f"nh-stat-value grad" if variant == "brand" else f"nh-stat-value {variant}"
        col.markdown(f"""
        <div class="nh-stat {variant}">
          <div class="nh-stat-icon {variant}">{icon_html}</div>
          <div class="{val_cls}">{s['value']}</div>
          <div class="nh-stat-label">{s['label']}</div>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# ANIMATED SCORE RING (Pure CSS SVG)
# ─────────────────────────────────────────────────────────────────────────────

def score_hero(pct: float, label: str = "COMPATIBILITY SCORE"):
    """Animated SVG circular score ring — no matplotlib."""
    cls = score_class(pct)
    dec = decision_from_score(pct)
    bc  = badge_class(dec)
    bi  = badge_icon(dec)

    r    = 57
    circ = 2 * math.pi * r
    off  = circ * (1 - pct / 100)

    p = _palette()
    if cls == "hire":
        grad_def = f'<linearGradient id="sg" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="{p["success"]}"/><stop offset="100%" stop-color="{p["accent"]}"/></linearGradient>'
    elif cls == "consider":
        grad_def = f'<linearGradient id="sg" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="{p["warn"]}"/><stop offset="100%" stop-color="{p["danger"]}"/></linearGradient>'
    else:
        grad_def = f'<linearGradient id="sg" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="{p["danger"]}"/><stop offset="100%" stop-color="{p["brand2"]}"/></linearGradient>'

    decision_label = {"HIRE": "Strong Fit", "CONSIDER": "Potential Fit", "REJECT": "Low Fit"}.get(dec, dec)

    st.markdown(f"""
    <div class="nh-score-ring-wrap">
      <div class="nh-score-ring">
        <svg viewBox="0 0 154 154" width="154" height="154">
          <defs>{grad_def}</defs>
          <circle class="track" cx="77" cy="77" r="{r}"/>
          <circle class="arc {cls}" cx="77" cy="77" r="{r}"
            stroke="url(#sg)"
            stroke-dasharray="{circ:.2f}"
            stroke-dashoffset="{off:.2f}"
            style="transform-origin:center;transform:rotate(-90deg);
                   transition:stroke-dashoffset 1.3s cubic-bezier(0.4,0,0.2,1);"/>
        </svg>
        <div class="nh-score-center">
          <div class="nh-score-num {cls}">{pct:.0f}<span class="nh-score-unit">%</span></div>
        </div>
      </div>
      <div class="nh-score-ring-label">{label}</div>
      <div style="display:flex;justify-content:center;margin-top:4px;">
        <span class="nh-badge {bc}">{bi}&nbsp;{decision_label}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PREMIUM TABLES AND EMPTY STATES
# ─────────────────────────────────────────────────────────────────────────────

def empty_state(icon_key: str, title: str, description: str):
    """Renders a premium empty state when there is no data."""
    icon_html = ICONS.get(icon_key, ICONS["alert"])
    st.markdown(f"""
    <div class="nh-empty">
      <div class="nh-empty-icon"><div style="width:44px;height:44px;">{icon_html}</div></div>
      <div class="nh-empty-title">{title}</div>
      <div class="nh-empty-desc">{description}</div>
    </div>
    """, unsafe_allow_html=True)

def _get_initials(name: str) -> str:
    parts = name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    elif len(parts) == 1 and len(parts[0]) > 0:
        return parts[0][0].upper()
    return "??"

def premium_table(headers: List[str], rows: List[List[str]], avatars_col: int = -1):
    """
    Renders a custom HTML table using the premium CSS classes.
    avatars_col: If specified, the column index that contains a name, which will be rendered with an avatar.
    """
    html = '<div class="nh-premium-table-container"><table class="nh-premium-table"><thead><tr>'
    
    # Headers
    for header in headers:
        html += f"<th>{header}</th>"
    html += "</tr></thead><tbody>"
    
    # Rows
    for row in rows:
        html += "<tr>"
        for i, cell in enumerate(row):
            if i == avatars_col and cell and str(cell).strip():
                name = str(cell)
                initials = _get_initials(name)
                bg_color, text_color = _avatar_bg(name)
                html += f"""
                <td>
                  <div class="avatar-cell">
                    <div class="avatar" style="background: {bg_color}; color: {text_color}; border: 1px solid {text_color}40;">
                      {initials}
                    </div>
                    <div class="primary-text">{name}</div>
                  </div>
                </td>
                """
            else:
                html += f"<td>{cell}</td>"
        html += "</tr>"
    
    html += "</tbody></table></div>"
    st.markdown(html, unsafe_allow_html=True)


def progress_mini(pct: float) -> str:
    """Returns HTML for a mini inline progress bar."""
    color = score_color(pct)
    return f"""
    <div class="nh-progress-container">
      <div class="nh-progress-mini">
        <div class="nh-progress-mini-bar" style="width: {min(pct,100):.0f}%; background: {color};"></div>
      </div>
      <div class="nh-progress-mini-text" style="color: {color};">{pct:.0f}%</div>
    </div>
    """

def badge_html(text: str, status_type: str = "draft") -> str:
    """Returns HTML for an inline status badge."""
    icon = ""
    if status_type == "hire": icon = ICONS["check"]
    elif status_type == "consider": icon = ICONS["alert"]
    elif status_type == "reject": icon = ICONS["x"]
    elif status_type == "active": icon = ICONS["play"]
    elif status_type == "closed": icon = ICONS["x"]
    elif status_type == "draft": icon = ICONS["file-text"]
    
    return f'<span class="nh-badge-inline {status_type}">{icon} {text}</span>'


# ─────────────────────────────────────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────────────────────────────────────

def draw_donut(score: float, label: str = "", size: float = 3.2):
    """Donut chart, theme-aware."""
    p = _palette()
    fig, ax = plt.subplots(figsize=(size, size), subplot_kw={"aspect": "equal"})
    fig.patch.set_facecolor(p["bg"])
    ax.set_facecolor(p["bg"])
    color = score_color(score)
    ax.pie([score, 100 - score], startangle=90,
           colors=[color, p["grid"]],
           wedgeprops={"width": 0.28, "edgecolor": p["bg"], "linewidth": 2},
           counterclock=False)
    ax.text(0, 0.08, f"{score:.0f}%", ha="center", va="center",
            fontsize=20 if size >= 3 else 13, fontweight="bold",
            color=p["text"], fontfamily="DejaVu Sans")
    if label:
        ax.text(0, -0.28, label[:20], ha="center", va="center",
                fontsize=6.5, color=p["muted"], fontfamily="DejaVu Sans")
    ax.axis("off")
    plt.tight_layout(pad=0)
    st.pyplot(fig, clear_figure=True)


def draw_radar(radar_data: Dict, size: float = 4.5):
    """Competency radar chart, theme-aware."""
    p = _palette()
    labels = radar_data.get("labels", [])
    cv_s   = radar_data.get("cv_scores", [])
    job_s  = radar_data.get("job_requirements", [])
    if not labels or len(labels) < 3:
        st.caption("Insufficient data for chart.")
        return

    n      = len(labels)
    angles = [x / float(n) * 2 * math.pi for x in range(n)] + [0]
    cv_v   = [v / 100 for v in cv_s]  + [cv_s[0]  / 100]
    job_v  = [v / 100 for v in job_s] + [job_s[0] / 100]

    fig, ax = plt.subplots(figsize=(size, size), subplot_kw={"projection": "polar"})
    fig.patch.set_facecolor(p["bg"])
    ax.set_facecolor(p["bg"])
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels([])
    ax.yaxis.grid(True, color=p["grid"], linewidth=1)
    ax.xaxis.grid(True, color=p["grid"], linewidth=1)
    ax.spines["polar"].set_color(p["grid"])

    ax.fill(angles, job_v, color=p["accent"], alpha=0.06)
    ax.plot(angles, job_v, color=p["accent"], linewidth=1.5, linestyle="--", alpha=0.6)
    ax.fill(angles, cv_v,  color=p["brand"], alpha=0.14)
    ax.plot(angles, cv_v,  color=p["brand"], linewidth=2.2)
    ax.scatter(angles[:-1], cv_v[:-1], color=p["brand"], s=30, zorder=5,
               edgecolors=p["bg"], linewidths=1.5)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=7.5, color=p["label"])
    ax.set_ylim(0, 1)

    legend_items = [
        mpatches.Patch(color=p["brand"],  label="Candidate"),
        mpatches.Patch(color=p["accent"], label="Required"),
    ]
    ax.legend(handles=legend_items, loc="upper right",
              bbox_to_anchor=(1.36, 1.16), fontsize=7.5,
              framealpha=0, labelcolor=p["label"])
    plt.tight_layout(pad=0.2)
    st.pyplot(fig, clear_figure=True)


def draw_component_bars(comp_scores: Dict):
    """Horizontal bar chart showing AI score breakdown, theme-aware."""
    if not comp_scores:
        return
    p = _palette()

    rows = []
    for k, v in comp_scores.items():
        name  = SCORE_LABELS.get(k, k.replace("_score", "").upper())
        color = MODEL_COLORS.get(k.replace("_score", "").upper(), p["brand"])
        rows.append((name, round(float(v) * 100, 1), color))

    if not rows:
        return

    fig, ax = plt.subplots(figsize=(5, max(1.8, len(rows) * 0.72)))
    fig.patch.set_facecolor(p["bg"])
    ax.set_facecolor(p["bg"])

    names  = [r[0] for r in rows]
    scores = [r[1] for r in rows]
    colors = [r[2] for r in rows]

    bars = ax.barh(names, scores, color=colors, height=0.42, edgecolor=p["bg"])
    for bar, val in zip(bars, scores):
        ax.text(min(val + 1.5, 92), bar.get_y() + bar.get_height() / 2,
                f"{val:.0f}%", va="center", fontsize=8.5,
                color=p["text"], fontweight="bold", fontfamily="DejaVu Sans")

    ax.set_xlim(0, 100)
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
    ax.axvline(75, color=p["success"], linestyle="--", alpha=0.35, linewidth=1)
    ax.axvline(55, color=p["warn"], linestyle="--", alpha=0.35, linewidth=1)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.tick_params(axis="x", colors=p["muted"], labelsize=7)
    ax.tick_params(axis="y", colors=p["label"], labelsize=8.5)
    plt.tight_layout(pad=0.3)
    st.pyplot(fig, clear_figure=True)


def draw_model_comparison_chart(rows: List[Dict]):
    """Model comparison bar chart with recruiter-friendly labels, theme-aware."""
    p = _palette()
    fig, ax = plt.subplots(figsize=(8, 2.8))
    fig.patch.set_facecolor(p["bg"])
    ax.set_facecolor(p["bg"])

    names  = [MODEL_LABELS.get(r["Model"], r["Model"]) for r in rows]
    scores = [r["Score (%)"] for r in rows]
    colors = [MODEL_COLORS.get(r["Model"], p["brand"]) for r in rows]

    bars = ax.barh(names, scores, color=colors, height=0.5, edgecolor=p["bg"])
    for bar, val in zip(bars, scores):
        ax.text(min(val + 1.5, 92), bar.get_y() + bar.get_height() / 2,
                f"{val:.0f}%", va="center", fontsize=9,
                color=p["text"], fontweight="bold", fontfamily="DejaVu Sans")

    ax.set_xlim(0, 100)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(p["grid"])
    ax.tick_params(colors=p["label"], labelsize=9)
    ax.axvline(75, color=p["success"], linestyle="--", alpha=0.4, linewidth=1)
    ax.axvline(55, color=p["warn"], linestyle="--", alpha=0.4, linewidth=1)
    ax.text(75.5, -0.75, "Strong Fit",    color=p["success"], fontsize=6.5, alpha=0.8)
    ax.text(55.5, -0.75, "Potential Fit", color=p["warn"], fontsize=6.5, alpha=0.8)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.tick_params(axis="x", colors=p["muted"], labelsize=7.5)
    plt.tight_layout(pad=0.2)
    st.pyplot(fig, clear_figure=True)


def draw_ranking_chart(ranked: List[Dict]):
    """Horizontal ranking bar chart, theme-aware."""
    if not ranked:
        return
    p = _palette()

    fig, ax = plt.subplots(figsize=(8, max(2.4, len(ranked) * 0.62 + 0.8)))
    fig.patch.set_facecolor(p["bg"])
    ax.set_facecolor(p["bg"])

    names  = [r["Name"] for r in ranked]
    scores = [r["Score"] for r in ranked]
    colors = [score_color(s) for s in scores]

    bars = ax.barh(names, scores, color=colors, height=0.5, edgecolor=p["bg"])
    for bar, val in zip(bars, scores):
        ax.text(min(val + 1.5, 92), bar.get_y() + bar.get_height() / 2,
                f"{val:.0f}%", va="center", fontsize=8.5,
                color=p["text"], fontweight="bold", fontfamily="DejaVu Sans")

    ax.set_xlim(0, 100)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(p["grid"])
    ax.tick_params(colors=p["label"], labelsize=8.5)
    ax.axvline(75, color=p["success"], linestyle="--", alpha=0.35, linewidth=1)
    ax.axvline(55, color=p["warn"], linestyle="--", alpha=0.35, linewidth=1)
    ax.invert_yaxis()
    plt.tight_layout(pad=0.3)
    st.pyplot(fig, clear_figure=True)


# ─────────────────────────────────────────────────────────────────────────────
# SKILL CHIPS
# ─────────────────────────────────────────────────────────────────────────────

def skill_chips(skills: List[str], chip_class: str, prefix: str = "") -> str:
    if not skills:
        return '<span style="color:var(--text-faint);font-size:0.8rem;">None detected</span>'
    return " ".join(f'<span class="{chip_class}">{prefix}{s}</span>' for s in skills)


def skill_section(skill_analysis: Dict):
    """Premium 4-panel skills analysis with recruiter-friendly labels."""
    matched  = skill_analysis.get("matching_skills", [])
    missing  = skill_analysis.get("missing_skills", [])
    extra    = skill_analysis.get("extra_skills", [])
    critical = skill_analysis.get("critical_missing", [])
    coverage = skill_analysis.get("skill_coverage", "N/A")

    col1, col2 = st.columns(2)
    with col1:
        section_label("check", "DETECTED SKILLS")
        st.markdown(skill_chips(matched, "nh-chip nh-chip-match", ""), unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        section_label("star", "ADDITIONAL SKILLS")
        st.markdown(skill_chips(extra, "nh-chip nh-chip-extra", ""), unsafe_allow_html=True)
    with col2:
        section_label("x", "MISSING REQUIREMENTS")
        st.markdown(skill_chips(missing, "nh-chip nh-chip-missing", ""), unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        section_label("alert", "PRIORITY GAPS")
        st.markdown(skill_chips(critical, "nh-chip nh-chip-critical", ""), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="nh-summary-row">
      <div class="nh-summary-item">
        <div class="nh-summary-val" style="color:var(--success-ink)!important;">{len(matched)}</div>
        <div class="nh-summary-label">Matched</div>
      </div>
      <div class="nh-summary-item">
        <div class="nh-summary-val" style="color:var(--danger-ink)!important;">{len(missing)}</div>
        <div class="nh-summary-label">Missing</div>
      </div>
      <div class="nh-summary-item">
        <div class="nh-summary-val" style="color:var(--warn-ink)!important;">{len(critical)}</div>
        <div class="nh-summary-label">Priority</div>
      </div>
      <div class="nh-summary-item">
        <div class="nh-summary-val" style="color:var(--brand-ink)!important;">{coverage}</div>
        <div class="nh-summary-label">Coverage</div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# AI INSIGHT PANEL  (recruiter language replacing "AI Oracle")
# ─────────────────────────────────────────────────────────────────────────────

def ai_recommendation_panel(hiring_rec: Dict, pct: float):
    """Recruiter-facing AI insight panel. No technical jargon."""
    if not hiring_rec:
        return
    decision = hiring_rec.get("decision", "CONSIDER")
    just     = hiring_rec.get("justification", "")
    conf_raw = float(hiring_rec.get("confidence", 0.7))
    conf     = int(round(conf_raw * 100))
    level    = hiring_rec.get("confidence_level", "")

    panel_cls = {
        "HIRE":    "nh-insight-hire",
        "CONSIDER":"nh-insight-consider",
        "REJECT":  "nh-insight-reject",
    }.get(decision, "nh-insight-consider")

    eyebrow_map = {
        "HIRE":    "AI EVALUATION · STRONG FIT",
        "CONSIDER":"AI EVALUATION · POTENTIAL FIT",
        "REJECT":  "AI EVALUATION · LOW FIT",
    }

    st.markdown(f"""
    <div class="nh-insight {panel_cls}">
      <div class="nh-insight-eyebrow">{ICONS['brain']} &nbsp; {eyebrow_map.get(decision,'AI EVALUATION')}</div>
      <div class="nh-insight-body">{just}</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-size:0.7rem;font-weight:700;color:var(--text-muted);'
        f'text-transform:uppercase;letter-spacing:.1em;margin:10px 0 4px;">'
        f'Decision Confidence · {level.title()} ({conf}%)</div>',
        unsafe_allow_html=True,
    )
    st.progress(max(0.0, min(1.0, conf_raw)))
    st.caption(
        "Uncalibrated — reflects how far the score sits from the decision "
        "threshold. It is not a probability of hire or of on-the-job success."
    )


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE CARD
# ─────────────────────────────────────────────────────────────────────────────

def feature_card(icon_key: str, icon_variant: str, title: str, desc: str) -> str:
    icon_html = ICONS.get(icon_key, "")
    return f"""
    <div class="nh-feature">
      <div class="nh-feature-icon {icon_variant}">{icon_html}</div>
      <div class="nh-feature-title">{title}</div>
      <div class="nh-feature-desc">{desc}</div>
    </div>
    """


# ─────────────────────────────────────────────────────────────────────────────
# ARCHITECTURE TABLE
# ─────────────────────────────────────────────────────────────────────────────

def architecture_table():
    """Technology stack displayed in recruiter-facing language where possible."""
    rows = [
        ("Semantic AI",       "Sentence Embedding",     "Understands CV meaning, not just words"),
        ("Multilingual",      "Cross-language Support",  "Matches across English & French"),
        ("Skill Detection",   "NLP Extraction",          "Identifies skills from unstructured text"),
        ("Keyword Match",     "Statistical Analysis",    "Precise term and phrase alignment"),
        ("Smart Scoring",     "Weighted Ensemble",       "Balanced, accurate compatibility score"),
        ("Explainability",    "Gap Analysis Engine",     "Generates actionable improvement steps"),
        ("Report Export",     "PDF Generation",          "Enterprise-quality printable reports"),
        ("API Layer",         "REST API",                "Integration-ready endpoint access"),
    ]
    html = "".join(f"""
    <div class="nh-arch-row">
      <div class="nh-arch-layer">{layer}</div>
      <div class="nh-arch-tech">{tech}</div>
      <div class="nh-arch-desc">{desc}</div>
    </div>
    """ for layer, tech, desc in rows)
    st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# RANKING CARD
# ─────────────────────────────────────────────────────────────────────────────

def ranking_card(rank: int, name: str, score: float, decision: str,
                 matched: List[str], critical: List[str]) -> str:
    rank_cls    = {1: "rank-1", 2: "rank-2", 3: "rank-3"}.get(rank, "")
    rank_label  = {1: "#1", 2: "#2", 3: "#3"}.get(rank, f"#{rank}")
    bc          = badge_class(decision)
    bi          = badge_icon(decision)
    fill_cls    = f"nh-rank-fill-{decision.lower()}"
    score_pct   = min(score, 100)

    # Avatar
    initials = "".join(w[0].upper() for w in name.split()[:2]) or "?"
    bg, fg   = _avatar_bg(name)
    avatar   = (
        f'<div style="width:38px;height:38px;border-radius:50%;'
        f'background:{bg};border:1px solid {fg};display:flex;'
        f'align-items:center;justify-content:center;'
        f'font-size:0.82rem;font-weight:700;color:{fg};flex-shrink:0;">'
        f'{initials}</div>'
    )

    dec_label  = {"HIRE": "Strong Fit", "CONSIDER": "Potential Fit", "REJECT": "Low Fit"}.get(decision, decision)
    matched_h  = " ".join(f'<span class="nh-chip nh-chip-match">{s}</span>' for s in matched[:5]) or '<span style="color:var(--text-faint);font-size:0.8rem;">—</span>'
    critical_h = " ".join(f'<span class="nh-chip nh-chip-critical">{s}</span>' for s in critical[:3]) or '<span style="color:var(--text-faint);font-size:0.8rem;">None</span>'

    return f"""
    <div class="nh-rank-card {rank_cls}">
      <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap;">
        <div class="nh-rank-num">{rank_label}</div>
        {avatar}
        <div style="flex:1;min-width:150px;">
          <div class="nh-rank-name">{name}</div>
          <div class="nh-rank-bar">
            <div class="nh-rank-fill {fill_cls}" style="width:{score_pct:.0f}%"></div>
          </div>
          <div style="font-size:0.7rem;color:var(--text-muted);margin-top:2px;font-variant-numeric:tabular-nums;">{score:.1f}% compatibility</div>
        </div>
        <div style="text-align:right;flex-shrink:0;">
          <span class="nh-badge {bc}">{bi}&nbsp;{dec_label}</span>
        </div>
      </div>
      <div style="margin-top:12px;padding-top:12px;border-top:1px solid var(--border);display:flex;gap:20px;flex-wrap:wrap;">
        <div style="flex:1;min-width:120px;">
          <div style="font-size:0.58rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.12em;margin-bottom:6px;font-weight:700;">Matching Skills</div>
          {matched_h}
        </div>
        <div style="flex:1;min-width:120px;">
          <div style="font-size:0.58rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.12em;margin-bottom:6px;font-weight:700;">Priority Gaps</div>
          {critical_h}
        </div>
      </div>
    </div>
    """


# ─────────────────────────────────────────────────────────────────────────────
# SWOT / STRENGTHS & GAPS SECTION
# ─────────────────────────────────────────────────────────────────────────────

def swot_section(gap_analysis: Dict, experience_fit: Dict):
    strengths = gap_analysis.get("strengths", [])
    blocking  = gap_analysis.get("blocking_gaps", [])
    minor     = gap_analysis.get("minor_gaps", [])

    col1, col2 = st.columns(2)
    with col1:
        section_label("check", "STRENGTHS")
        if strengths:
            for s in strengths:
                st.markdown(f"""
                <div class="nh-alert nh-alert-success">
                  <span class="nh-alert-icon">{ICONS['check']}</span>
                  <span>{s}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.caption("No strengths data available.")

        if experience_fit:
            st.markdown("<br>", unsafe_allow_html=True)
            section_label("clock", "EXPERIENCE PROFILE")
            fit_status  = experience_fit.get("fit_status", "N/A")
            candidate_y = experience_fit.get("candidate_years", 0)
            required_y  = experience_fit.get("estimated_required_years", 3)
            edu         = experience_fit.get("education_level", "Unknown")
            st.markdown(f"""
            <div class="nh-card nh-card-sm" style="margin-top:8px;">
              <div style="font-size:0.88rem;font-weight:700;color:var(--text-primary)!important;margin-bottom:10px;">{fit_status}</div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:0.78rem;">
                <div><span style="color:var(--text-muted);">Detected:</span> <span style="color:var(--brand-ink)!important;">{candidate_y:.0f}y experience</span></div>
                <div><span style="color:var(--text-muted);">Required:</span> <span style="color:var(--brand-ink)!important;">~{required_y:.0f}y</span></div>
                <div style="grid-column:span 2;"><span style="color:var(--text-muted);">Education:</span> <span style="color:var(--brand-ink)!important;">{edu}</span></div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        section_label("x", "CRITICAL GAPS")
        if blocking:
            for g in blocking:
                st.markdown(f"""
                <div class="nh-alert nh-alert-error">
                  <span class="nh-alert-icon">{ICONS['x']}</span>
                  <span>{g}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="nh-alert nh-alert-success">
              <span class="nh-alert-icon">{ICONS['check']}</span>
              <span>No critical gaps identified</span>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        section_label("alert", "MINOR GAPS")
        if minor:
            for g in minor:
                st.markdown(f"""
                <div class="nh-alert nh-alert-warning">
                  <span class="nh-alert-icon">{ICONS['alert']}</span>
                  <span>{g}</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.caption("No minor gaps.")


# ─────────────────────────────────────────────────────────────────────────────
# RECOMMENDATIONS SECTION
# ─────────────────────────────────────────────────────────────────────────────

def recommendations_section(reco: Dict):
    import pandas as pd
    actions = reco.get("priority_actions", [])

    c1, c2, c3 = st.columns(3)
    c1.metric("Time to Close Gap", reco.get("learning_time_estimate", "N/A"))
    c2.metric("Match Potential",   reco.get("match_potential", "N/A"))
    c3.metric("Missing Keywords",  str(len(reco.get("keywords_to_add", []))))

    st.markdown("<br>", unsafe_allow_html=True)
    section_label("target", "SUGGESTED ACTIONS")
    if actions:
        df = pd.DataFrame(actions)
        df.columns = [c.replace("_", " ").title() for c in df.columns]
        if "Resource" in df.columns:
            df["Resource"] = df["Resource"].apply(lambda u: f"[Link]({u})" if u else "—")
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.caption("No suggested actions available.")

    keywords = reco.get("keywords_to_add", [])
    if keywords:
        st.markdown("<br>", unsafe_allow_html=True)
        section_label("search", "RECOMMENDED KEYWORDS FOR CV")
        st.markdown(" ".join(f'<span class="nh-chip nh-chip-extra">{k}</span>' for k in keywords),
                    unsafe_allow_html=True)

    improvements = reco.get("cv_improvements", [])
    if improvements:
        st.markdown("<br>", unsafe_allow_html=True)
        section_label("info", "PROFILE IMPROVEMENT TIPS")
        for tip in improvements:
            st.markdown(f"""
            <div class="nh-alert nh-alert-info">
              <span class="nh-alert-icon">{ICONS['arrow-right']}</span>
              <span style="font-size:0.875rem;">{tip}</span>
            </div>""", unsafe_allow_html=True)
