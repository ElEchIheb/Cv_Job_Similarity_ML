"""
frontend/decision_state.py
Single accessor for the ACTIVE decision configuration in the Streamlit session.

Settings writes the recruiter's chosen thresholds here; Candidate Analysis,
Talent Leaderboard, Bulk Evaluation and the UI badge helpers all read from here,
so one configuration governs every surface within a session. Falls back to the
canonical defaults when unset.
"""
from __future__ import annotations

from src.decisioning import DecisionConfig, DEFAULT_STRONG_FIT, DEFAULT_POTENTIAL_FIT

_SESSION_KEY = "decision_config"


def get_active_config() -> DecisionConfig:
    """Return the active DecisionConfig from session state (or defaults)."""
    try:
        import streamlit as st
        raw = st.session_state.get(_SESSION_KEY)
        if isinstance(raw, dict):
            return DecisionConfig.make(
                raw.get("potential_fit_threshold", DEFAULT_POTENTIAL_FIT),
                raw.get("strong_fit_threshold", DEFAULT_STRONG_FIT),
            )
    except Exception:
        pass
    return DecisionConfig.default()


def set_active_config(potential: float, strong: float) -> DecisionConfig:
    """Validate and store thresholds in session state. Raises on invalid input."""
    import streamlit as st
    cfg = DecisionConfig.make(potential, strong)   # validates
    st.session_state[_SESSION_KEY] = cfg.as_dict()
    return cfg
