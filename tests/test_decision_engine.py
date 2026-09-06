"""Tests for the canonical DecisionEngine — the single source of truth."""
import math
import pytest

from src.decisioning import (
    DecisionEngine, DecisionConfig, HIRE, CONSIDER, REJECT,
    DEFAULT_STRONG_FIT, DEFAULT_POTENTIAL_FIT,
)
from src.decisioning.decision_engine import DecisionConfigError


@pytest.fixture
def engine():
    return DecisionEngine(DecisionConfig.default())


# ── Boundary semantics ───────────────────────────────────────────────────────
@pytest.mark.parametrize("pct, expected", [
    (0,   REJECT),
    (54.9, REJECT),
    (55,  CONSIDER),      # at potential threshold -> CONSIDER
    (55.0001, CONSIDER),
    (74.9, CONSIDER),
    (75,  HIRE),          # at strong threshold -> HIRE
    (90,  HIRE),
    (100, HIRE),
])
def test_classify_boundaries(engine, pct, expected):
    assert engine.classify(pct) == expected


def test_below_potential_is_reject(engine):
    assert engine.classify(9) == REJECT      # the old "9% -> HIRE" bug is gone
    assert engine.classify(46) == REJECT     # the old "46% -> HIRE" bug is gone


def test_fraction_and_percentage_equivalent(engine):
    # 0.83 (fraction) and 83 (percentage) must classify identically
    assert engine.classify(0.83) == engine.classify(83) == HIRE
    assert engine.classify(0.40) == engine.classify(40) == REJECT


# ── Configurable thresholds ──────────────────────────────────────────────────
def test_custom_thresholds_change_decision():
    strict = DecisionEngine(DecisionConfig.make(potential=60, strong=85))
    assert strict.classify(80) == CONSIDER   # 80 < 85 strong
    lenient = DecisionEngine(DecisionConfig.make(potential=40, strong=60))
    assert lenient.classify(65) == HIRE


# ── Validation ───────────────────────────────────────────────────────────────
@pytest.mark.parametrize("potential, strong", [
    (75, 75),      # equal
    (80, 70),      # potential > strong
    (-1, 75),      # negative
    (55, 101),     # > 100
])
def test_invalid_config_rejected(potential, strong):
    with pytest.raises(DecisionConfigError):
        DecisionConfig.make(potential, strong)


def test_nan_rejected():
    with pytest.raises(DecisionConfigError):
        DecisionConfig.make(float("nan"), 75)


def test_bool_rejected():
    with pytest.raises(DecisionConfigError):
        DecisionConfig.make(True, 75)


# ── Confidence semantics ─────────────────────────────────────────────────────
def test_confidence_is_zero_on_boundary(engine):
    assert engine.decision_confidence(75) == 0.0
    assert engine.decision_confidence(55) == 0.0


def test_confidence_in_unit_interval(engine):
    for pct in range(0, 101, 7):
        c = engine.decision_confidence(pct)
        assert 0.0 <= c <= 1.0


def test_confidence_grows_away_from_boundary(engine):
    near = engine.decision_confidence(76)
    far = engine.decision_confidence(95)
    assert far > near


# ── Determinism / reproducibility ────────────────────────────────────────────
def test_same_input_same_output(engine):
    a = engine.evaluate(0.6846)
    b = engine.evaluate(0.6846)
    assert a.as_dict() == b.as_dict()


def test_evaluate_carries_thresholds(engine):
    r = engine.evaluate(80)
    assert r.strong_fit_threshold == DEFAULT_STRONG_FIT
    assert r.potential_fit_threshold == DEFAULT_POTENTIAL_FIT
    assert r.decision == HIRE
    assert r.band_label == "Strong Fit"
