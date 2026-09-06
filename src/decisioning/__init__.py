"""
src/decisioning
Canonical decision layer for NeuralHire.

Exposes the single source of truth for turning a compatibility score into a
recruiter-facing decision (HIRE / CONSIDER / REJECT), together with an
uncalibrated *decision confidence* and a human-readable explanation.
"""
from .decision_engine import (
    DecisionConfig,
    DecisionEngine,
    DecisionResult,
    DEFAULT_STRONG_FIT,
    DEFAULT_POTENTIAL_FIT,
    HIRE,
    CONSIDER,
    REJECT,
)

__all__ = [
    "DecisionConfig",
    "DecisionEngine",
    "DecisionResult",
    "DEFAULT_STRONG_FIT",
    "DEFAULT_POTENTIAL_FIT",
    "HIRE",
    "CONSIDER",
    "REJECT",
]
