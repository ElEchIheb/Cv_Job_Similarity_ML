"""
Score scale, calibration and verdict coherence across API / database / PDF.

The AI models are replaced by deterministic fakes so the tests check the
product chain itself: raw score -> versioned calibration -> DecisionEngine ->
persisted MatchResult -> history / overview -> PDF, plus legacy results,
invalid inputs and recruiter isolation.
"""
from __future__ import annotations

import io
import json
import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.decisioning import DecisionConfig, DecisionEngine, CONSIDER, HIRE, REJECT
from src.decisioning.calibration import (
    CalibrationError, MethodCalibration, ScoreCalibration, UNCALIBRATED_VERSION, load_calibration,
)

ROOT = Path(__file__).resolve().parents[1]
CAL = ScoreCalibration(
    version="test-v1",
    methods={
        "hybrid": MethodCalibration("hybrid", cut_consider=0.25, cut_hire=0.40, ceiling=0.60),
        "tfidf": MethodCalibration("tfidf", cut_consider=0.05, cut_hire=0.15, ceiling=0.45),
    },
)


# ── Calibration maths ────────────────────────────────────────────────────────
def test_anchors_map_to_reference_bounds():
    cal = CAL.methods["hybrid"]
    assert cal.to_display(0.0) == 0.0
    assert cal.to_display(0.25) == 55.0
    assert cal.to_display(0.40) == 75.0
    assert cal.to_display(0.60) == 100.0
    assert cal.to_display(0.95) == 100.0          # clipped above the ceiling
    assert cal.to_display(float("nan")) == 0.0
    assert cal.to_display(-1) == 0.0


def test_calibration_is_monotone():
    cal = CAL.methods["hybrid"]
    values = [cal.to_display(x / 1000) for x in range(0, 1001)]
    assert all(a <= b for a, b in zip(values, values[1:]))


@pytest.mark.parametrize("cuts", [(0.3, 0.2, 0.6), (0.2, 0.2, 0.6), (0.2, 0.4, 0.3), (0.0, 0.4, 0.6)])
def test_non_monotone_anchors_are_rejected(cuts):
    with pytest.raises(CalibrationError):
        MethodCalibration("hybrid", *cuts)


def test_unknown_method_is_explicitly_uncalibrated():
    assert CAL.version_for("embedding") == UNCALIBRATED_VERSION
    assert CAL.to_display("embedding", 0.42) == 42.0


def test_round_trip_serialisation():
    again = ScoreCalibration.from_dict(json.loads(json.dumps(CAL.to_dict())))
    assert again.to_dict() == CAL.to_dict()


def test_shipped_calibration_file_is_valid():
    """The production calibration covers every selectable method."""
    path = ROOT / "models" / "checkpoints" / "score_calibration.json"
    assert path.exists(), "run evaluation/calibration_study.py final"
    cal = load_calibration(str(path))
    assert cal.is_calibrated and cal.version.startswith("synthetic-")
    assert set(cal.methods) == {"hybrid", "tfidf", "embedding", "skill"}
    assert "warning" in cal.provenance


# ── Verdict frontiers through the real scoring service ──────────────────────
def _fake_models(raw: float, critical=None):
    details = {
        "score": raw, "matching_skills": ["python"], "missing_skills": [], "extra_skills": [],
        "critical_missing": list(critical or []), "same_domain": True,
        "coverage": {"skill_coverage_text": "1/1 required skills"},
        "cv_payload": {"hard_skills": ["python"], "soft_skills": [], "certifications": [],
                       "years_experience": 5, "education_level": "master", "domain": "data"},
        "job_payload": {"hard_skills": ["python"], "soft_skills": [], "certifications": [],
                        "years_experience": 3, "education_level": "master", "domain": "data"},
    }
    hybrid = MagicMock()
    hybrid.predict.return_value = {
        "final_score": raw, "component_scores": {"tfidf_score": 0.1, "embedding_score": 0.5, "skill_score": 0.3},
        "weights_used": {"tfidf": 0.2, "embedding": 0.4, "skill": 0.4}, "skill_details": details,
    }
    single = MagicMock()
    single.predict.return_value = raw
    skill = MagicMock()
    skill.predict.return_value = raw
    skill.predict_detailed.return_value = details
    extractor = MagicMock()
    extractor.extract.return_value = details["cv_payload"]
    from src.explainability.explainer import MatchingExplainer, RecommendationEngine
    return {"hybrid": hybrid, "tfidf": single, "embedding": single, "skill": skill,
            "explainer": MatchingExplainer(extractor=extractor), "recommender": RecommendationEngine(),
            "calibration": CAL}


@pytest.mark.parametrize("raw,expected", [
    (0.249, REJECT), (0.25, CONSIDER), (0.399, CONSIDER), (0.40, HIRE), (0.0, REJECT), (0.9, HIRE),
])
def test_verdict_frontiers_on_calibrated_scale(raw, expected):
    from src.matching.service import run_evaluation
    payload = run_evaluation(_fake_models(raw), "cv text " * 5, "job text", "hybrid")
    assert payload["decision"].decision == expected
    assert payload["explanation"]["hiring_recommendation"]["decision"] == expected
    assert payload["result"]["raw_score"] == round(raw, 4)
    assert payload["result"]["calibration_version"] == "test-v1"


def test_verdict_follows_the_displayed_rounded_score():
    """The engine classifies the score the recruiter sees (rounded to 0.1)."""
    from src.matching.service import run_evaluation
    payload = run_evaluation(_fake_models(0.2499), "cv text " * 5, "job text", "hybrid")
    assert payload["result"]["percentage"] == 55.0
    assert payload["decision"].decision == CONSIDER


def test_tiny_raw_score_is_not_rescaled_to_hire():
    """Regression for the 0-1/0-100 ambiguity: a 0.009 TF-IDF score used to be HIRE."""
    from src.matching.service import run_evaluation
    payload = run_evaluation(_fake_models(0.009), "cv text " * 5, "job text", "tfidf")
    assert payload["decision"].decision == REJECT


# ── API / DB / PDF coherence ────────────────────────────────────────────────
@pytest.fixture
def api(monkeypatch):
    fastapi = pytest.importorskip("fastapi.testclient")
    import src.api.main as main
    import src.models_db as m
    from src.database import get_db

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    m.Base.metadata.create_all(bind=engine)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    state = {"raw": 0.30}
    monkeypatch.setattr(main, "_get_services", lambda: _fake_models(state["raw"]))
    main.app.dependency_overrides[get_db] = override
    client = fastapi.TestClient(main.app)

    def login(prefix):
        email = f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"
        client.post("/api/v1/auth/register", json={"email": email, "password": "password123", "full_name": "R"})
        token = client.post("/api/v1/auth/login", data={"username": email, "password": "password123"}).json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def job(headers):
        r = client.post("/api/v1/ui/job-offers", json={"title": "Data Engineer", "description": "Python SQL Airflow",
                                                       "required_skills": "python, sql"}, headers=headers)
        assert r.status_code == 200, r.text
        return r.json()["id"]

    yield {"client": client, "login": login, "job": job, "state": state, "Session": Session}
    main.app.dependency_overrides.clear()
    m.Base.metadata.drop_all(bind=engine)


CV = "Data engineer with five years of Python, SQL and Airflow pipelines in production."


def test_evaluate_persists_calibrated_score_and_version(api):
    c, h = api["client"], api["login"]("a")
    job_id = api["job"](h)
    r = c.post("/api/v1/ui/evaluate", json={"cv_text": CV, "job_offer_id": job_id}, headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    expected_pct = CAL.to_display("hybrid", 0.30)                     # 61.7
    assert body["result"]["percentage"] == expected_pct
    assert body["decision"]["decision"] == CONSIDER == body["explanation"]["hiring_recommendation"]["decision"]

    rows = c.get("/api/v1/ui/matches", headers=h).json()
    assert len(rows) == 1
    row = rows[0]
    assert row["decision"] == CONSIDER
    assert row["final_score"] == pytest.approx(expected_pct / 100, abs=1e-4)
    assert row["score_raw"] == pytest.approx(0.30)
    assert row["calibration_version"] == "test-v1" and row["legacy_scale"] is False
    assert (row["potential_fit_threshold"], row["strong_fit_threshold"]) == (55.0, 75.0)

    detail = c.get(f"/api/v1/ui/matches/{row['id']}", headers=h).json()
    assert detail["decision"] == CONSIDER and detail["calibration_version"] == "test-v1"
    assert detail["explanation"]["hiring_recommendation"]["decision"] == CONSIDER


def test_custom_thresholds_are_applied_and_saved(api):
    c, h = api["client"], api["login"]("b")
    job_id = api["job"](h)
    r = c.post("/api/v1/ui/evaluate", json={"cv_text": CV, "job_offer_id": job_id,
                                            "potential_fit_threshold": 40, "strong_fit_threshold": 60}, headers=h)
    assert r.json()["decision"]["decision"] == HIRE                    # 61.7 >= 60
    row = c.get("/api/v1/ui/matches", headers=h).json()[0]
    assert (row["potential_fit_threshold"], row["strong_fit_threshold"]) == (40.0, 60.0)


def test_pdf_report_carries_the_same_decision_and_scale(api):
    c, h = api["client"], api["login"]("c")
    job_id = api["job"](h)
    body = c.post("/api/v1/ui/evaluate", json={"cv_text": CV, "job_offer_id": job_id}, headers=h).json()
    r = c.post("/api/v1/report/pdf", json={"result": body["result"], "explanation": body["explanation"],
                                           "recommendations": body["recommendations"],
                                           "candidate_name": "Test", "job_title": "Data Engineer"}, headers=h)
    if r.status_code == 501:
        pytest.skip("reportlab not installed")
    assert r.status_code == 200
    from PyPDF2 import PdfReader
    text = " ".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(r.content)).pages)
    flat = " ".join(text.split())
    assert "test-v1" in flat
    assert "not a probability" in flat
    assert "CONSIDER" in flat


def test_legacy_results_are_flagged_and_kept_out_of_aggregates(api):
    c, h = api["client"], api["login"]("d")
    job_id = api["job"](h)
    c.post("/api/v1/ui/evaluate", json={"cv_text": CV, "job_offer_id": job_id}, headers=h)
    import src.models_db as m
    db = api["Session"]()
    current = db.query(m.MatchResult).first()
    legacy = m.MatchResult(candidate_id=current.candidate_id, job_offer_id=job_id, final_score=0.95,
                           decision="HIRE", model_version="hybrid-checkpoint-v2", calibration_version=None)
    db.add(legacy)
    db.commit()
    legacy_id = legacy.id
    db.close()

    rows = {r["id"]: r for r in c.get("/api/v1/ui/matches", headers=h).json()}
    assert rows[legacy_id]["legacy_scale"] is True and rows[legacy_id]["score_scale"] == "legacy"
    assert rows[legacy_id]["decision"] == "HIRE"                      # kept as recorded, not re-derived

    ov = c.get("/api/v1/ui/overview", headers=h).json()
    assert ov["legacy_matches"] == 1 and ov["current_scale_matches"] == 1
    assert ov["avg_score"] == pytest.approx(CAL.to_display("hybrid", 0.30) / 100, abs=1e-4)
    assert ov["hire_count"] == 0

    cand = c.get("/api/v1/ui/candidates", headers=h).json()[0]
    assert cand["best_score"] == pytest.approx(CAL.to_display("hybrid", 0.30) / 100, abs=1e-4)
    assert cand["legacy_evaluation_count"] == 1


@pytest.mark.parametrize("payload,status", [
    ({"cv_text": ""}, 400),
    ({"cv_text": "too short cv"}, 400),
    ({"cv_text": CV, "potential_fit_threshold": 80, "strong_fit_threshold": 60}, 400),
    ({"cv_text": CV, "potential_fit_threshold": 55, "strong_fit_threshold": 120}, 422),
    ({"cv_text": CV, "model": "random"}, 422),
])
def test_invalid_evaluation_inputs(api, payload, status):
    c, h = api["client"], api["login"]("e")
    job_id = api["job"](h)
    r = c.post("/api/v1/ui/evaluate", json={"job_offer_id": job_id, **payload}, headers=h)
    assert r.status_code == status, r.text


def test_invalid_documents_are_rejected(api):
    c, h = api["client"], api["login"]("f")
    job_id = api["job"](h)
    r = c.post("/api/v1/ui/evaluate/file", data={"job_offer_id": str(job_id)},
               files={"cv_file": ("cv.txt", b"plain text cv with enough words here", "text/plain")}, headers=h)
    assert r.status_code == 400
    r = c.post("/api/v1/ui/evaluate/file", data={"job_offer_id": str(job_id)},
               files={"cv_file": ("cv.pdf", b"%PDF-1.4 not really a pdf", "application/pdf")}, headers=h)
    assert r.status_code == 400


def test_recruiters_are_isolated(api):
    c = api["client"]
    a, b = api["login"]("iso_a"), api["login"]("iso_b")
    job_a = api["job"](a)
    match_id = c.post("/api/v1/ui/evaluate", json={"cv_text": CV, "job_offer_id": job_a}, headers=a).json()["match_id"]
    assert c.post("/api/v1/ui/evaluate", json={"cv_text": CV, "job_offer_id": job_a}, headers=b).status_code == 404
    assert c.get(f"/api/v1/ui/matches/{match_id}", headers=b).status_code == 404
    assert c.get("/api/v1/ui/matches", headers=b).json() == []
    assert c.get("/api/v1/ui/candidates", headers=b).json() == []


def test_frontend_does_not_rederive_verdicts_from_hardcoded_thresholds():
    """Verdict bands must come from the backend DecisionEngine, not from 75/55
    literals compared in UI code (the AI Insights page used to do this)."""
    import re
    pattern = re.compile(r"(percentage|pct|score)\s*>=\s*(75|55)\b")
    offenders = []
    for path in list((ROOT / "web" / "app").rglob("*.tsx")) + list((ROOT / "web" / "components").rglob("*.tsx")):
        if pattern.search(path.read_text(encoding="utf-8")):
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []
