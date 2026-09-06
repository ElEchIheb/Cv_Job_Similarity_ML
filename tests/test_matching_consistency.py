"""
Consistency tests: the explainer's decision must equal the DecisionEngine's,
and persistence must de-duplicate candidates/jobs and store reproducibility
metadata. No heavy AI models are loaded (synthetic payloads + in-memory DB).
"""
import json
from unittest.mock import MagicMock

import pytest

from src.decisioning import DecisionEngine, DecisionConfig, HIRE, CONSIDER, REJECT
from src.explainability.explainer import MatchingExplainer


def _fake_extractor():
    m = MagicMock()
    m.extract.return_value = {
        "hard_skills": ["python"], "soft_skills": [], "certifications": [],
        "years_experience": 5, "education_level": "master", "domain": "data",
    }
    return m


def _hybrid_result(pct: float):
    frac = pct / 100.0
    return {
        "final_score": frac,
        "percentage": pct,
        "component_scores": {"tfidf_score": frac, "embedding_score": frac, "skill_score": frac},
        "weights_used": {"tfidf": 0.2, "embedding": 0.4, "skill": 0.4},
        "skill_details": {
            "score": frac, "matching_skills": ["python"], "missing_skills": [],
            "extra_skills": [], "critical_missing": [],
            "same_domain": True, "coverage": {"skill_coverage_text": "1/1 required skills"},
            "cv_payload": _fake_extractor().extract.return_value,
            "job_payload": _fake_extractor().extract.return_value,
        },
    }


@pytest.mark.parametrize("pct", [5, 40, 55, 60, 74, 75, 83, 95])
def test_explainer_decision_matches_engine(pct):
    explainer = MatchingExplainer(extractor=_fake_extractor())
    cfg = DecisionConfig.default()
    expl = explainer.explain("cv text here", "job text here", _hybrid_result(pct), config=cfg)
    engine_decision = DecisionEngine(cfg).classify(pct)
    assert expl["hiring_recommendation"]["decision"] == engine_decision


def test_explainer_respects_custom_config():
    explainer = MatchingExplainer(extractor=_fake_extractor())
    cfg = DecisionConfig.make(potential=40, strong=60)
    expl = explainer.explain("cv", "job", _hybrid_result(65), config=cfg)
    assert expl["hiring_recommendation"]["decision"] == HIRE


# ── Persistence + de-duplication ─────────────────────────────────────────────
@pytest.fixture
def db():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.database import Base
    import src.models_db  # noqa: F401 — register models on Base
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    Session = sessionmaker(bind=eng)
    s = Session()
    yield s
    s.close()


def _payload(pct: float, cfg: DecisionConfig):
    engine = DecisionEngine(cfg)
    return {
        "result": _hybrid_result(pct),
        "explanation": {"skill_analysis": {"matching_skills": ["python"], "missing_skills": ["sql"]},
                        "hiring_recommendation": {}, "gap_analysis": {}},
        "recommendations": {},
        "decision": engine.evaluate(pct, cfg),
        "config": cfg,
        "model_key": "hybrid",
    }


def test_persist_reuses_named_candidate_and_job(db):
    from src.matching.service import persist_evaluation
    import src.models_db as m
    cfg = DecisionConfig.default()

    job = m.JobOffer(job_code="JOB-A", title="Data Engineer", description="Desc")
    db.add(job)
    db.commit()
    db.refresh(job)

    persist_evaluation(db, _payload(80, cfg), "cv1", "Alice Martin", "alice@test.com", job.id, 1)
    persist_evaluation(db, _payload(85, cfg), "cv2", "Alice Martin", "alice@test.com", job.id, 1)

    assert db.query(m.Candidate).count() == 1
    assert db.query(m.JobOffer).count() == 1
    assert db.query(m.MatchResult).count() == 2
    assert db.query(m.CV).count() == 2


def test_persist_generates_stable_anonymous_ids(db):
    from src.matching.service import persist_evaluation
    import src.models_db as m
    cfg = DecisionConfig.default()

    job = m.JobOffer(job_code="JOB-B", title="Job A", description="Desc")
    db.add(job)
    db.commit()
    db.refresh(job)

    persist_evaluation(db, _payload(80, cfg), "cvA", None, None, job.id, 1)
    persist_evaluation(db, _payload(80, cfg), "cvB", None, None, job.id, 1)

    cands = db.query(m.Candidate).all()
    assert len(cands) == 2
    assert cands[0].is_anonymous == 1
    assert cands[0].full_name == "Candidate #2026-001"
    assert cands[1].full_name == "Candidate #2026-002"


def test_persist_stores_reproducibility_metadata(db):
    from src.matching.service import persist_evaluation
    import src.models_db as m
    cfg = DecisionConfig.make(potential=50, strong=80)

    job = m.JobOffer(job_code="JOB-C", title="Eng", description="Desc")
    db.add(job)
    db.commit()
    db.refresh(job)

    match = persist_evaluation(db, _payload(85, cfg), "cv", "Bob", "bob@test.com", job.id, 1)
    assert match.model_version == "hybrid-checkpoint-v2"
    assert match.strong_fit_threshold == 80
    assert match.potential_fit_threshold == 50
    assert match.evaluation_method == "hybrid"
    assert match.decision_confidence is not None
    assert match.candidate_id is not None and match.job_offer_id is not None
