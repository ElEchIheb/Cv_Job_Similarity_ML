"""
src/decisioning/calibration.py
Versioned score calibration: raw similarity score (0-1) -> displayed score (0-100).

Why a calibration layer exists
------------------------------
The matching methods return raw similarities that do not share a scale: a
cosine between two different documents rarely exceeds ~0.8, TF-IDF overlaps
stay below ~0.5, and the 0.2/0.4/0.4 fusion cannot reach 0.75 even when every
component is at its observed maximum. Reading ``raw * 100`` against the
recruiter bands (55 / 75) therefore produced almost only REJECT verdicts.

The calibration is a monotone piecewise-linear map per method with three
anchors learned on the *validation* split only:

    raw 0                -> 0
    raw ``cut_consider`` -> reference CONSIDER bound (55)
    raw ``cut_hire``     -> reference HIRE bound (75)
    raw ``ceiling``      -> 100   (clipped above)

It preserves the ranking of candidates (same AUC), keeps the explanation
untouched (sub-scores stay raw) and is fully described by three numbers per
method, stored with a version string in ``models/checkpoints/score_calibration.json``.
Every persisted result records the version used.

Important limit: the anchors were learned on synthetic labels. They make the
displayed bands consistent with the benchmark's ordinal classes (strong /
transferable / unrelated); they are NOT a validated hiring policy and must be
re-fitted on annotated real data before operational use.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger("jobtest.calibration")

UNCALIBRATED_VERSION = "uncalibrated"
DEFAULT_PATH = Path(__file__).resolve().parents[2] / "models" / "checkpoints" / "score_calibration.json"


class CalibrationError(ValueError):
    """Raised when a calibration file is malformed or non-monotone."""


@dataclass(frozen=True)
class MethodCalibration:
    method: str
    cut_consider: float
    cut_hire: float
    ceiling: float
    consider_display: float = 55.0
    hire_display: float = 75.0

    def __post_init__(self) -> None:
        points = (0.0, self.cut_consider, self.cut_hire, self.ceiling)
        if not all(a < b for a, b in zip(points, points[1:])):
            raise CalibrationError(
                f"{self.method}: anchors must satisfy 0 < cut_consider < cut_hire < ceiling, got {points}.")
        if not (0.0 < self.consider_display < self.hire_display < 100.0):
            raise CalibrationError(f"{self.method}: display anchors must satisfy 0 < consider < hire < 100.")

    def to_display(self, raw: float) -> float:
        """Map a raw 0-1 score to the displayed 0-100 scale (monotone, clipped)."""
        try:
            x = float(raw)
        except (TypeError, ValueError):
            x = 0.0
        if x != x:  # NaN
            x = 0.0
        x = max(0.0, x)
        xs = (0.0, self.cut_consider, self.cut_hire, self.ceiling)
        ys = (0.0, self.consider_display, self.hire_display, 100.0)
        if x >= xs[-1]:
            return 100.0
        for (x0, y0), (x1, y1) in zip(zip(xs, ys), zip(xs[1:], ys[1:])):
            if x <= x1:
                return round(y0 + (x - x0) * (y1 - y0) / (x1 - x0), 1)
        return 100.0  # pragma: no cover - unreachable

    def as_dict(self) -> Dict[str, float]:
        return {
            "cut_consider": self.cut_consider,
            "cut_hire": self.cut_hire,
            "ceiling": self.ceiling,
            "consider_display": self.consider_display,
            "hire_display": self.hire_display,
        }


@dataclass(frozen=True)
class ScoreCalibration:
    version: str
    methods: Dict[str, MethodCalibration] = field(default_factory=dict)
    provenance: Dict[str, object] = field(default_factory=dict)

    @property
    def is_calibrated(self) -> bool:
        return self.version != UNCALIBRATED_VERSION

    def to_display(self, method: str, raw: float) -> float:
        cal = self.methods.get(method)
        if cal is None:
            # Explicit, visible fallback: the result is tagged "uncalibrated".
            return round(max(0.0, min(100.0, float(raw or 0.0) * 100.0)), 1)
        return cal.to_display(raw)

    def version_for(self, method: str) -> str:
        return self.version if method in self.methods else UNCALIBRATED_VERSION

    def summary(self) -> Dict[str, object]:
        return {
            "version": self.version,
            "calibrated": self.is_calibrated,
            "methods": {k: v.as_dict() for k, v in self.methods.items()},
            "provenance": self.provenance,
        }

    @classmethod
    def from_dict(cls, payload: Dict) -> "ScoreCalibration":
        try:
            version = str(payload["version"])
            methods = {
                name: MethodCalibration(method=name, **{k: float(v) for k, v in spec.items()})
                for name, spec in payload["methods"].items()
            }
        except (KeyError, TypeError) as exc:
            raise CalibrationError(f"Malformed calibration payload: {exc}") from exc
        return cls(version=version, methods=methods, provenance=dict(payload.get("provenance", {})))

    def to_dict(self) -> Dict[str, object]:
        return {
            "version": self.version,
            "methods": {k: v.as_dict() for k, v in self.methods.items()},
            "provenance": self.provenance,
        }


UNCALIBRATED = ScoreCalibration(version=UNCALIBRATED_VERSION)


@lru_cache(maxsize=4)
def load_calibration(path: Optional[str] = None) -> ScoreCalibration:
    """Load the versioned calibration; fall back (loudly) to the identity scale."""
    file_path = Path(path) if path else DEFAULT_PATH
    if not file_path.exists():
        logger.warning("Score calibration file %s not found — scores are UNCALIBRATED (raw x 100).", file_path)
        return UNCALIBRATED
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    calibration = ScoreCalibration.from_dict(payload)
    logger.info("Score calibration loaded: %s (%s)", calibration.version, ", ".join(calibration.methods))
    return calibration
