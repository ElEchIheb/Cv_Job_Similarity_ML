from __future__ import annotations

import numpy as np
import pandas as pd

from src.evaluation.evaluator import EvaluationSuite


def _dataset() -> pd.DataFrame:
    rows = []
    for index in range(40):
        label = index % 2
        # Rows 0/1 deliberately share a pair, exercising group-level splitting.
        pair_id = 0 if index in {0, 1} else index
        rows.append({
            "cv_text": f"Candidate {pair_id} Python FastAPI",
            "job_text": f"Backend role {pair_id} Python FastAPI",
            "label": label if index not in {0, 1} else 0,
            "domain": "Backend",
        })
    return pd.DataFrame(rows)


def test_stratified_split_keeps_duplicate_pairs_together():
    split = EvaluationSuite.stratified_split(_dataset())

    EvaluationSuite.assert_pair_groups_disjoint(split)
    duplicate_counts = [
        int((part["cv_text"] == "Candidate 0 Python FastAPI").sum())
        for part in (split.train, split.validation, split.test)
    ]
    assert sorted(duplicate_counts) == [0, 0, 2]


def test_threshold_calibration_uses_native_score_scale():
    threshold = EvaluationSuite.calibrate_threshold(
        np.asarray([0, 0, 1, 1]), np.asarray([0.04, 0.12, 0.31, 0.45])
    )
    assert threshold == 0.31


def test_operating_point_warning_catches_high_auc_near_zero_f1():
    warnings = EvaluationSuite.operating_point_warnings({
        "tfidf": {"roc_auc": 0.98, "f1": 0.0},
        "hybrid": {"roc_auc": 0.80, "f1": 0.50},
    })
    assert len(warnings) == 1
    assert "tfidf" in warnings[0]
