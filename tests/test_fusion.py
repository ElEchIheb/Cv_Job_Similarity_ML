"""
tests/test_fusion.py
Tests for HybridMatcher — uses session-scoped fixtures to avoid
repeated model cold-starts (which cause PyTorch threading issues on Python 3.13).
"""
from __future__ import annotations

import pandas as pd
import pytest


def _sample_df():
    rows = [
        {"cv_text": "Python ML engineer with mlflow docker kubernetes", "job_text": "Required python mlflow docker kubernetes", "label": 1, "domain": "AI / NLP Engineering"},
        {"cv_text": "Frontend react developer with typescript and figma", "job_text": "React typescript figma communication", "label": 1, "domain": "Frontend Development"},
        {"cv_text": "Cybersecurity analyst with siem soc owasp", "job_text": "SIEM SOC OWASP incident response", "label": 1, "domain": "Cybersecurity"},
        {"cv_text": "Data scientist with pandas pytorch", "job_text": "Angular frontend role with css and figma", "label": 0, "domain": "Frontend Development"},
        {"cv_text": "Mobile engineer with swift ios", "job_text": "DevOps kubernetes terraform aws", "label": 0, "domain": "DevOps / Cloud Engineering"},
        {"cv_text": "Backend java spring boot kafka", "job_text": "Security engineer owasp nmap siem", "label": 0, "domain": "Cybersecurity"},
    ]
    return pd.DataFrame(rows)


def test_hybrid_predict_returns_expected_shape(hybrid_matcher):
    hybrid_matcher.models["tfidf"].fit(["Python ML engineer with mlflow docker kubernetes", "Required python mlflow docker kubernetes"])
    """Uses session-scoped fixture — no repeated model loading."""
    result = hybrid_matcher.predict("Python ML engineer with mlflow", "Required python mlflow docker")
    assert "final_score" in result
    assert "component_scores" in result
    assert 0.0 <= result["final_score"] <= 1.0


def test_hybrid_optimize_weights_returns_normalized_weights(hybrid_matcher):
    df = _sample_df()
    outcome = hybrid_matcher.optimize_weights(
        df.iloc[:4].reset_index(drop=True),
        df.iloc[4:].reset_index(drop=True),
        step=0.5,
    )
    total = sum(outcome["best_weights"].values())
    assert round(total, 3) == 1.0
    assert "validation_metrics" in outcome
