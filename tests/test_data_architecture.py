import pytest
from src.database import Base, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src import models_db
from src.matching.service import _resolve_candidate, persist_evaluation
from src.decisioning import DecisionConfig, DecisionResult

# In-memory SQLite for testing
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        # Create a test recruiter
        user = models_db.User(email="test@recruiter.com", hashed_password="hash", full_name="Test Recruiter")
        db.add(user)
        db.commit()
        db.refresh(user)
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_candidate_deduplication_by_email(db_session):
    recruiter_id = 1
    # Create first candidate
    cand1, created1 = _resolve_candidate(db_session, "Alice", "alice@test.com", recruiter_id)
    assert created1 is True
    assert cand1.email == "alice@test.com"
    
    # Try creating with same email
    cand2, created2 = _resolve_candidate(db_session, "Alice Smith", "ALICE@test.com", recruiter_id)
    assert created2 is False
    assert cand2.id == cand1.id
    assert cand2.email == "alice@test.com"


class MockDecision:
    def __init__(self, decision, confidence, confidence_level):
        self.decision = decision
        self.confidence = confidence
        self.confidence_level = confidence_level

def test_persist_evaluation_requires_job_offer(db_session):
    recruiter_id = 1
    payload = {
        "result": {"final_score": 0.85, "component_scores": {}},
        "explanation": {"hiring_recommendation": {}},
        "recommendations": [],
        "decision": MockDecision("HIRE", 0.8, "high"),
        "config": DecisionConfig.default(),
        "model_key": "hybrid"
    }
    
    # Must raise ValueError if job offer does not exist
    with pytest.raises(ValueError, match="JobOffer with id 999 not found"):
        persist_evaluation(db_session, payload, "CV Text", "Bob", "bob@test.com", 999, recruiter_id)


def test_persist_evaluation_links_correctly(db_session):
    recruiter_id = 1
    job = models_db.JobOffer(job_code="JOB-TEST", title="Engineer", description="Desc", recruiter_id=recruiter_id)
    db_session.add(job)
    db_session.commit()
    
    payload = {
        "result": {"final_score": 0.85, "component_scores": {}},
        "explanation": {"hiring_recommendation": {}},
        "recommendations": [],
        "decision": MockDecision("HIRE", 0.8, "high"),
        "config": DecisionConfig.default(),
        "model_key": "hybrid"
    }
    
    match = persist_evaluation(db_session, payload, "CV Text", "Bob", "bob@test.com", job.id, recruiter_id)
    
    assert match.candidate.email == "bob@test.com"
    assert match.candidate.full_name == "Bob"
    assert match.job_offer_id == job.id
    assert match.job_offer.job_code == "JOB-TEST"
