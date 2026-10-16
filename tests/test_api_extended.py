"""
tests/test_api_extended.py
Extended API tests for the upgraded JobTest backend (v2).
"""
from __future__ import annotations

import pytest

try:
    from fastapi.testclient import TestClient
    from src.api.main import app
    _API_AVAILABLE = app is not None
except Exception:
    _API_AVAILABLE = False

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.database import get_db, Base

engine_test = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client():
    if not _API_AVAILABLE:
        pytest.skip("FastAPI or app not available")
    from fastapi.testclient import TestClient
    from src.api.main import app
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def db_setup():
    import src.models_db as m
    m.Base.metadata.create_all(bind=engine_test)
    yield
    m.Base.metadata.drop_all(bind=engine_test)

def _register_and_login(client, prefix: str) -> dict:
    import uuid
    email = f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/api/v1/auth/register", json={"email": email, "password": "password123", "full_name": "Test User"})
    resp = client.post("/api/v1/auth/login", data={"username": email, "password": "password123"})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def auth_headers(client, db_setup):
    """Recruiter A — owns the job offer used by the matching tests."""
    return _register_and_login(client, "recruiter_a")


@pytest.fixture
def other_auth_headers(client, db_setup):
    """Recruiter B — a second, unrelated account used for access-control checks."""
    return _register_and_login(client, "recruiter_b")


@pytest.fixture
def mock_db_job_a(client, auth_headers):
    """Job offer created through the API, hence owned by recruiter A.

    Since the ownership checks (IDOR guard), a job inserted directly in the
    database without ``recruiter_id`` is invisible to every recruiter, so the
    fixture must go through the authenticated endpoint.
    """
    from types import SimpleNamespace
    resp = client.post("/api/v1/job-offers", json={
        "title": "Backend Developer",
        "description": "Required: Python, Django",
        "required_skills": "Python, Django",
    }, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    return SimpleNamespace(**resp.json())


CV_SAMPLE  = "Python developer with 5 years experience. Skills: Python, Django, PostgreSQL, Docker, AWS."
JOB_SAMPLE = "Backend developer needed: Python, Django, PostgreSQL required. Docker and AWS preferred."


class TestHealthEndpoints:
    def test_health_basic(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "models" in data
        assert "version" in data

    def test_health_detailed(self, client):
        resp = client.get("/api/v1/health/detailed")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "model_status" in data
        assert "config" in data
        assert "match_threshold" in data["config"]

    def test_metrics(self, client):
        resp = client.get("/api/v1/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "requests_total" in data


class TestMatchEndpoints:
    def test_match_hybrid(self, client, auth_headers, mock_db_job_a):
        resp = client.post("/api/v1/match", json={
            "cv_text": CV_SAMPLE,
            "job_offer_id": mock_db_job_a.id,
            "model": "hybrid",
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "final_score" in data
        assert "decision" in data
        assert "job_offer_id" in data

    def test_match_embedding(self, client, auth_headers, mock_db_job_a):
        resp = client.post("/api/v1/match", json={
            "cv_text": CV_SAMPLE,
            "job_offer_id": mock_db_job_a.id,
            "model": "embedding",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert "final_score" in resp.json()

    def test_match_invalid_model(self, client, auth_headers, mock_db_job_a):
        resp = client.post("/api/v1/match", json={
            "cv_text": CV_SAMPLE,
            "job_offer_id": mock_db_job_a.id,
            "model": "random_model",
        }, headers=auth_headers)
        assert resp.status_code == 422

    def test_match_empty_cv(self, client, auth_headers, mock_db_job_a):
        resp = client.post("/api/v1/match", json={
            "cv_text": "",
            "job_offer_id": mock_db_job_a.id,
        }, headers=auth_headers)
        assert resp.status_code == 422

    def test_match_explanation_structure(self, client, auth_headers, mock_db_job_a):
        resp = client.post("/api/v1/match", json={
            "cv_text": CV_SAMPLE,
            "job_offer_id": mock_db_job_a.id,
            "model": "hybrid",
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "explanation" in data
        explanation = data["explanation"]
        assert "hiring_recommendation" in explanation
        assert "gap_analysis" in explanation


class TestRankEndpoint:
    def test_rank_candidates(self, client, auth_headers, mock_db_job_a):
        resp = client.post("/api/v1/rank", json={
            "job_offer_id": mock_db_job_a.id,
            "candidates": [
                {"name": "Alice", "cv_text": CV_SAMPLE},
                {"name": "Bob",   "cv_text": "Java developer with Spring Boot experience"},
            ],
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "ranked" in data
        assert len(data["ranked"]) == 2
        assert data["ranked"][0]["candidate_name"] == "Alice"
        assert data["ranked"][0]["rank"] == 1

    def test_rank_returns_decision(self, client, auth_headers, mock_db_job_a):
        resp = client.post("/api/v1/rank", json={
            "job_offer_id": mock_db_job_a.id,
            "candidates": [{"name": "Alice", "cv_text": CV_SAMPLE}],
        }, headers=auth_headers)
        assert resp.status_code == 200
        ranked = resp.json()["ranked"]
        assert len(ranked) == 1
        assert "decision" in ranked[0]
        assert ranked[0]["decision"] in {"HIRE", "CONSIDER", "REJECT", "N/A"}


class TestPDFEndpoint:
    def test_pdf_returns_bytes(self, client, auth_headers, mock_db_job_a):
        # We need a match result first to generate PDF
        match_resp = client.post("/api/v1/match", json={
            "cv_text": CV_SAMPLE,
            "job_offer_id": mock_db_job_a.id,
            "model": "hybrid",
        }, headers=auth_headers)
        assert match_resp.status_code == 200
        
        resp = client.post("/api/v1/report/pdf", json={
            "result": match_resp.json(),
            "explanation": match_resp.json().get("explanation", {}),
            "recommendations": match_resp.json().get("recommendations", {}),
            "candidate_name": "Test Candidate",
            "job_title": "Backend Developer"
        }, headers=auth_headers)
        
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        if resp.status_code == 501:
            pytest.skip("reportlab not installed")
        assert "Test Candidate" in resp.headers.get("content-disposition", "")


class TestRecruiterOwnership:
    """A recruiter must never read or score against another recruiter's job offer."""

    def test_other_recruiter_cannot_match_on_foreign_job(self, client, other_auth_headers, mock_db_job_a):
        resp = client.post("/api/v1/match", json={
            "cv_text": CV_SAMPLE,
            "job_offer_id": mock_db_job_a.id,
            "model": "hybrid",
        }, headers=other_auth_headers)
        assert resp.status_code == 404

    def test_other_recruiter_cannot_rank_on_foreign_job(self, client, other_auth_headers, mock_db_job_a):
        resp = client.post("/api/v1/rank", json={
            "job_offer_id": mock_db_job_a.id,
            "candidates": [{"name": "Alice", "cv_text": CV_SAMPLE}],
        }, headers=other_auth_headers)
        assert resp.status_code == 404

    def test_job_listing_is_scoped_to_owner(self, client, auth_headers, other_auth_headers, mock_db_job_a):
        own = client.get("/api/v1/job-offers", headers=auth_headers)
        foreign = client.get("/api/v1/job-offers", headers=other_auth_headers)
        assert own.status_code == 200 and foreign.status_code == 200
        assert mock_db_job_a.id in {j["id"] for j in own.json()}
        assert mock_db_job_a.id not in {j["id"] for j in foreign.json()}

    def test_orphan_job_without_owner_is_not_accessible(self, client, auth_headers, db_setup):
        import src.models_db as m
        db = TestingSessionLocal()
        orphan = m.JobOffer(job_code="ORPHAN-JOB", title="Orphan", description="Python")
        db.add(orphan)
        db.commit()
        orphan_id = orphan.id
        db.close()
        resp = client.post("/api/v1/match", json={
            "cv_text": CV_SAMPLE,
            "job_offer_id": orphan_id,
            "model": "hybrid",
        }, headers=auth_headers)
        assert resp.status_code == 404


class TestRateLimit:
    def test_rate_limit_returns_429_when_exceeded(self, client, monkeypatch):
        from src.config import settings
        monkeypatch.setattr(settings, "REQUEST_LIMIT_PER_MINUTE", 3)
        codes = [client.get("/api/v1/health").status_code for _ in range(4)]
        assert codes[:3] == [200, 200, 200]
        assert codes[3] == 429


def test_rank_breaks_ties_at_100_by_raw_score(client, auth_headers, mock_db_job_a, monkeypatch):
    """The calibration caps the display at 100: two CVs at 100 are ordered by raw score."""
    import src.api.main as api_main

    raws = {"cv-low": 0.62, "cv-high": 0.71}

    def fake(model_name, cv_text, job_text):
        return {"score": 1.0, "raw_score": raws[cv_text], "percentage": 100.0, "label": 1, "confidence": "high",
                "explanation": {"hiring_recommendation": {"decision": "HIRE"}}}

    monkeypatch.setattr(api_main, "_model_result", fake)
    resp = client.post("/api/v1/rank", json={
        "job_offer_id": mock_db_job_a.id,
        "candidates": [{"name": "A", "cv_text": "cv-low"}, {"name": "B", "cv_text": "cv-high"}],
    }, headers=auth_headers)
    assert resp.status_code == 200
    ranked = resp.json()["ranked"]
    assert [r["candidate_name"] for r in ranked] == ["B", "A"]
    assert [r["percentage"] for r in ranked] == [100.0, 100.0]
