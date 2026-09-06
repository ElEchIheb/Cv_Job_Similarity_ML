"""
src/decisioning/decision_engine.py
NeuralHire — Canonical Decision Engine (single source of truth).

This module is the ONLY place in the platform that maps a compatibility score
to a recruiter-facing decision. Every surface — Candidate Analysis, Talent
Leaderboard, Bulk Evaluation, Analysis History (display), Reports and the
Overview aggregates — must route decisions through this engine so that the
same (score, configuration) always yields the same decision.

Semantics
---------
Given a percentage score in [0, 100] and a configuration with two thresholds:

    score >= strong_fit_threshold                       -> HIRE      ("Strong Fit")
    potential_fit_threshold <= score < strong_fit       -> CONSIDER  ("Potential Fit")
    score <  potential_fit_threshold                    -> REJECT    ("Low Fit")

Decision confidence
-------------------
`decision_confidence` is an UNCALIBRATED measure of how far the score sits from
the nearest decision boundary (0 = right on a boundary, 1 = far inside a band).
It is NOT a probability that the candidate will be hired or will succeed, and
must never be labelled as such.

The engine has no heavy dependencies (pure Python) so it is trivially testable
and can never break the AI models.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

# Canonical decision labels (business terminology used across the platform)
HIRE = "HIRE"
CONSIDER = "CONSIDER"
REJECT = "REJECT"

# Human-friendly band names shown to recruiters
BAND_LABELS = {HIRE: "Strong Fit", CONSIDER: "Potential Fit", REJECT: "Low Fit"}

# Default active configuration. Matches the platform's documented policy and the
# thresholds advertised on the Settings page.
DEFAULT_STRONG_FIT = 75.0
DEFAULT_POTENTIAL_FIT = 55.0

# Width (in percentage points) used to normalise the uncalibrated confidence.
_CONFIDENCE_SPAN = 20.0


class DecisionConfigError(ValueError):
    """Raised when threshold configuration is invalid."""


@dataclass(frozen=True)
class DecisionConfig:
    """Immutable, validated threshold configuration.

    Invariant: 0 <= potential_fit_threshold < strong_fit_threshold <= 100.
    """

    strong_fit_threshold: float = DEFAULT_STRONG_FIT
    potential_fit_threshold: float = DEFAULT_POTENTIAL_FIT

    def __post_init__(self) -> None:
        self.validate(self.potential_fit_threshold, self.strong_fit_threshold)

    # ── Validation ──────────────────────────────────────────────────────────
    @staticmethod
    def validate(potential: float, strong: float) -> None:
        """Strictly validate thresholds; raise DecisionConfigError on failure."""
        for name, value in (("potential_fit_threshold", potential),
                            ("strong_fit_threshold", strong)):
            if value is None or isinstance(value, bool) or not isinstance(value, (int, float)):
                raise DecisionConfigError(f"{name} must be a number, got {value!r}.")
            # NaN check (NaN != NaN)
            if value != value:
                raise DecisionConfigError(f"{name} must not be NaN.")
            if value < 0 or value > 100:
                raise DecisionConfigError(f"{name} must be within [0, 100], got {value}.")
        if not (potential < strong):
            raise DecisionConfigError(
                f"potential_fit_threshold ({potential}) must be strictly less than "
                f"strong_fit_threshold ({strong})."
            )

    @classmethod
    def make(cls, potential, strong) -> "DecisionConfig":
        """Construct after validation. Validates the RAW inputs first (so wrong
        types such as bool/None/str are rejected before any float coercion)."""
        cls.validate(potential, strong)
        return cls(strong_fit_threshold=float(strong), potential_fit_threshold=float(potential))

    @classmethod
    def default(cls) -> "DecisionConfig":
        return cls()

    def as_dict(self) -> Dict[str, float]:
        return {
            "strong_fit_threshold": self.strong_fit_threshold,
            "potential_fit_threshold": self.potential_fit_threshold,
        }


@dataclass(frozen=True)
class DecisionResult:
    """The canonical outcome of classifying a single score."""

    decision: str                 # HIRE | CONSIDER | REJECT
    band_label: str               # Strong Fit | Potential Fit | Low Fit
    percentage: float             # score in [0, 100]
    confidence: float             # uncalibrated decision confidence in [0, 1]
    confidence_level: str         # high | medium | low
    reason: str                   # short human-readable justification
    strong_fit_threshold: float
    potential_fit_threshold: float

    def as_dict(self) -> Dict[str, object]:
        return asdict(self)


class DecisionEngine:
    """Stateless service: classify scores using a DecisionConfig."""

    def __init__(self, config: Optional[DecisionConfig] = None) -> None:
        self.config = config or DecisionConfig.default()

    # ── Normalisation helpers ────────────────────────────────────────────────
    @staticmethod
    def to_percentage(score: float) -> float:
        """Accept either a 0-1 fraction or a 0-100 percentage; return 0-100.

        A value in [0, 1] is treated as a fraction and scaled by 100. Values
        above 1 are treated as already being percentages. Result is clamped.
        """
        try:
            value = float(score)
        except (TypeError, ValueError):
            value = 0.0
        if value != value:  # NaN
            value = 0.0
        if 0.0 <= value <= 1.0:
            value *= 100.0
        return max(0.0, min(100.0, value))

    # ── Core classification ──────────────────────────────────────────────────
    def classify(self, score: float, config: Optional[DecisionConfig] = None) -> str:
        cfg = config or self.config
        pct = self.to_percentage(score)
        if pct >= cfg.strong_fit_threshold:
            return HIRE
        if pct >= cfg.potential_fit_threshold:
            return CONSIDER
        return REJECT

    def decision_confidence(self, score: float, config: Optional[DecisionConfig] = None) -> float:
        """Uncalibrated distance-from-boundary confidence in [0, 1].

        NOT a probability of hiring or success — purely how decisively the score
        sits inside its band relative to the nearest threshold.
        """
        cfg = config or self.config
        pct = self.to_percentage(score)
        nearest = min(abs(pct - cfg.potential_fit_threshold),
                      abs(pct - cfg.strong_fit_threshold))
        return round(max(0.0, min(1.0, nearest / _CONFIDENCE_SPAN)), 4)

    @staticmethod
    def confidence_level(confidence: float) -> str:
        if confidence >= 0.66:
            return "high"
        if confidence >= 0.33:
            return "medium"
        return "low"

    def evaluate(self, score: float, config: Optional[DecisionConfig] = None,
                 critical_missing: Optional[List[str]] = None) -> DecisionResult:
        """Full canonical evaluation of a single score."""
        cfg = config or self.config
        pct = round(self.to_percentage(score), 1)
        decision = self.classify(pct, cfg)
        conf = self.decision_confidence(pct, cfg)
        level = self.confidence_level(conf)
        reason = self._reason(pct, decision, cfg, critical_missing or [])
        return DecisionResult(
            decision=decision,
            band_label=BAND_LABELS[decision],
            percentage=pct,
            confidence=conf,
            confidence_level=level,
            reason=reason,
            strong_fit_threshold=cfg.strong_fit_threshold,
            potential_fit_threshold=cfg.potential_fit_threshold,
        )

    # ── Explanation ──────────────────────────────────────────────────────────
    @staticmethod
    def _reason(pct: float, decision: str, cfg: DecisionConfig,
                critical_missing: List[str]) -> str:
        blockers = ", ".join(critical_missing[:3]) if critical_missing else ""
        if decision == HIRE:
            base = (f"Overall compatibility of {pct:.0f}% is at or above the Strong Fit "
                    f"threshold ({cfg.strong_fit_threshold:.0f}%).")
            if critical_missing:
                base += f" Note: some required skills still need validation ({blockers})."
            return base + " Recommended to advance."
        if decision == CONSIDER:
            base = (f"Overall compatibility of {pct:.0f}% falls in the Potential Fit band "
                    f"({cfg.potential_fit_threshold:.0f}%–{cfg.strong_fit_threshold:.0f}%).")
            if critical_missing:
                base += f" Important requirements remain partially satisfied ({blockers})."
            return base + " Review before deciding."
        base = (f"Overall compatibility of {pct:.0f}% is below the Potential Fit threshold "
                f"({cfg.potential_fit_threshold:.0f}%).")
        if critical_missing:
            base += f" Critical requirements are missing ({blockers})."
        return base + " Not recommended without significant re-skilling."


# Module-level convenience singleton using the default configuration.
_DEFAULT_ENGINE = DecisionEngine()


def classify(score: float, config: Optional[DecisionConfig] = None) -> str:
    return _DEFAULT_ENGINE.classify(score, config)


def evaluate(score: float, config: Optional[DecisionConfig] = None,
             critical_missing: Optional[List[str]] = None) -> DecisionResult:
    return _DEFAULT_ENGINE.evaluate(score, config, critical_missing)
