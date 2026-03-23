from __future__ import annotations

from pathlib import Path

from src.models.embedding_model import EmbeddingMatcher
from src.models.skill_matcher import SkillMatcher
from src.models.tfidf_model import TFIDFMatcher


CV_TEXT = "Python backend engineer with FastAPI, Docker, PostgreSQL and strong communication."
JOB_TEXT = "Required: python, fastapi, docker, postgresql. Soft skills: communication, teamwork."


def test_tfidf_matcher_predict_and_persistence():
    matcher = TFIDFMatcher()
    score = matcher.predict(CV_TEXT, JOB_TEXT)
    assert 0.0 <= score <= 1.0

    base_dir = Path(__file__).resolve().parents[1] / "tests_tmp"
    base_dir.mkdir(exist_ok=True)
    file_path = base_dir / "tfidf.joblib"
    try:
        matcher.save(str(file_path))
        restored = TFIDFMatcher().load(str(file_path))
        assert 0.0 <= restored.predict(CV_TEXT, JOB_TEXT) <= 1.0
    finally:
        file_path.unlink(missing_ok=True)


def test_embedding_matcher_predicts_reasonable_score():
    matcher = EmbeddingMatcher()
    score = matcher.predict(CV_TEXT, JOB_TEXT)
    assert 0.0 <= score <= 1.0
    assert matcher.section_aware_similarity({"experience": CV_TEXT}, JOB_TEXT) >= 0.0


def test_skill_matcher_gap_analysis():
    matcher = SkillMatcher()
    job = "Must have python, fastapi, docker, kubernetes and communication."
    score = matcher.predict(CV_TEXT, job)
    missing = matcher.get_missing_skills()
    analysis = matcher.get_skill_gap_analysis()
    assert 0.0 <= score <= 1.0
    assert "kubernetes" in missing
    assert "critical_missing" in analysis
