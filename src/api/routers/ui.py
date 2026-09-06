"""
src/api/routers/ui.py

Additive HTTP router that exposes — over the same FastAPI app — the operations
the Streamlit UI performs in-process, so the Next.js frontend can reach full
functional parity WITHOUT re-implementing any business logic in the browser.

Design rules (per the parity mandate):
  * Every endpoint CALLS the existing, unchanged service/DB code
    (src.matching.service.evaluate_and_persist / run_evaluation, the same
    SQLAlchemy models, the same DecisionEngine). No algorithm, threshold, or
    schema is redefined here.
  * Behaviour mirrors the corresponding Streamlit page exactly (validation,
    ordering, delete-guards, job-code format, etc.).
  * All list/CRUD endpoints are recruiter-scoped, consistent with the existing
    /candidates, /job-offers and /matches endpoints.
"""
from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.config import settings
from src.database import get_db
from src import models_db
from src.security.auth import get_current_user
from src.decisioning import DecisionConfig
from src.decisioning.decision_engine import DecisionConfigError

router = APIRouter(prefix="/api/v1/ui", tags=["UI Parity"])

_ALLOWED_MODELS = {"hybrid", "embedding", "tfidf", "skill"}


# ── shared helpers ───────────────────────────────────────────────────────────
def _services() -> Dict:
    """Reuse the single lazily-loaded model cache from the main app."""
    from src.api.main import _get_services
    return _get_services()


def _job_text(job: models_db.JobOffer) -> str:
    """Exactly how the Streamlit pages build job_text for evaluation."""
    return f"{job.title}\n\n{job.description}\n\nRequired Skills: {job.required_skills_raw}"


def _next_job_code(db: Session) -> str:
    """Verbatim port of frontend/pages/job_offers.py::_next_job_code."""
    year = datetime.utcnow().year
    max_job = (
        db.query(models_db.JobOffer.job_code)
        .filter(models_db.JobOffer.job_code.like(f"JOB-{year}-%"))
        .order_by(models_db.JobOffer.job_code.desc())
        .first()
    )
    seq = 1
    if max_job and max_job[0]:
        try:
            seq = int(max_job[0].split("-")[-1]) + 1
        except ValueError:
            pass
    return f"JOB-{year}-{seq:03d}"


def _iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


def _config_from(strong: Optional[float], potential: Optional[float]) -> DecisionConfig:
    """Build the active DecisionConfig exactly like frontend.decision_state."""
    if strong is None and potential is None:
        return DecisionConfig.default()
    from src.decisioning import DEFAULT_STRONG_FIT, DEFAULT_POTENTIAL_FIT
    try:
        return DecisionConfig.make(
            potential if potential is not None else DEFAULT_POTENTIAL_FIT,
            strong if strong is not None else DEFAULT_STRONG_FIT,
        )
    except DecisionConfigError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid thresholds: {exc}") from exc


def _serialize_payload(payload: Dict) -> Dict:
    """Make the evaluate_and_persist payload JSON-safe for the frontend."""
    decision = payload.get("decision")
    config = payload.get("config")
    return {
        "result": payload.get("result"),
        "explanation": payload.get("explanation"),
        "recommendations": payload.get("recommendations"),
        "decision": decision.as_dict() if hasattr(decision, "as_dict") else decision,
        "config": config.as_dict() if hasattr(config, "as_dict") else config,
        "model_key": payload.get("model_key", "hybrid"),
        "match_id": payload.get("match_id"),
    }


# ═════════════════════════════════════════════════════════════════════════════
# OVERVIEW  (mirrors frontend/pages/dashboard.py stats — recruiter-scoped)
# ═════════════════════════════════════════════════════════════════════════════
@router.get("/overview")
def overview(db: Session = Depends(get_db), user: models_db.User = Depends(get_current_user)) -> Dict:
    cand_q = db.query(models_db.Candidate).filter(models_db.Candidate.recruiter_id == user.id)
    job_q = db.query(models_db.JobOffer).filter(models_db.JobOffer.recruiter_id == user.id)
    match_q = (
        db.query(models_db.MatchResult)
        .join(models_db.Candidate)
        .filter(models_db.Candidate.recruiter_id == user.id)
    )
    total_candidates = cand_q.count()
    total_jobs = job_q.count()
    total_matches = match_q.count()
    avg_score = (
        db.query(func.avg(models_db.MatchResult.final_score))
        .join(models_db.Candidate)
        .filter(models_db.Candidate.recruiter_id == user.id)
        .scalar()
    ) or 0
    hire_count = match_q.filter(models_db.MatchResult.decision == "HIRE").count()
    hire_pct = (hire_count / total_matches * 100) if total_matches > 0 else 0
    return {
        "total_candidates": total_candidates,
        "total_jobs": total_jobs,
        "total_matches": total_matches,
        "avg_score": float(avg_score),
        "hire_count": hire_count,
        "hire_pct": hire_pct,
    }


# ═════════════════════════════════════════════════════════════════════════════
# JOB OFFERS  (mirrors frontend/pages/job_offers.py)
# ═════════════════════════════════════════════════════════════════════════════
class JobOfferIn(BaseModel):
    title: str
    description: str
    required_skills: Optional[str] = ""
    status: Literal["OPEN", "ON_HOLD", "CLOSED"] = "OPEN"


def _job_dict(db: Session, o: models_db.JobOffer) -> Dict:
    count = db.query(models_db.MatchResult).filter(models_db.MatchResult.job_offer_id == o.id).count()
    return {
        "id": o.id,
        "job_code": o.job_code,
        "title": o.title,
        "description": o.description,
        "required_skills_raw": o.required_skills_raw or "",
        "status": (o.status or "OPEN"),
        "created_at": _iso(o.created_at),
        "evaluation_count": count,
    }


@router.get("/job-offers")
def list_job_offers(db: Session = Depends(get_db), user: models_db.User = Depends(get_current_user)) -> List[Dict]:
    offers = (
        db.query(models_db.JobOffer)
        .filter(models_db.JobOffer.recruiter_id == user.id)
        .order_by(models_db.JobOffer.created_at.desc())
        .all()
    )
    return [_job_dict(db, o) for o in offers]


@router.post("/job-offers")
def create_job_offer(body: JobOfferIn, db: Session = Depends(get_db), user: models_db.User = Depends(get_current_user)) -> Dict:
    if not body.title.strip() or not body.description.strip():
        raise HTTPException(status_code=400, detail="Title and Description are required.")
    job = models_db.JobOffer(
        job_code=_next_job_code(db),
        title=body.title.strip(),
        description=body.description.strip(),
        required_skills_raw=(body.required_skills or "").strip(),
        status=body.status,
        recruiter_id=user.id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return _job_dict(db, job)


def _owned_job(db: Session, job_id: int, user: models_db.User) -> models_db.JobOffer:
    job = (
        db.query(models_db.JobOffer)
        .filter(models_db.JobOffer.id == job_id, models_db.JobOffer.recruiter_id == user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job offer not found.")
    return job


@router.put("/job-offers/{job_id}")
def update_job_offer(job_id: int, body: JobOfferIn, db: Session = Depends(get_db), user: models_db.User = Depends(get_current_user)) -> Dict:
    job = _owned_job(db, job_id, user)
    if not body.title.strip() or not body.description.strip():
        raise HTTPException(status_code=400, detail="Title and Description are required.")
    job.title = body.title.strip()
    job.description = body.description.strip()
    job.required_skills_raw = (body.required_skills or "").strip()
    job.status = body.status
    db.commit()
    db.refresh(job)
    return _job_dict(db, job)


@router.post("/job-offers/{job_id}/toggle-status")
def toggle_job_status(job_id: int, db: Session = Depends(get_db), user: models_db.User = Depends(get_current_user)) -> Dict:
    job = _owned_job(db, job_id, user)
    job.status = "CLOSED" if job.status == "OPEN" else "OPEN"
    db.commit()
    db.refresh(job)
    return _job_dict(db, job)


@router.delete("/job-offers/{job_id}")
def delete_job_offer(job_id: int, db: Session = Depends(get_db), user: models_db.User = Depends(get_current_user)) -> Dict:
    job = _owned_job(db, job_id, user)
    count = db.query(models_db.MatchResult).filter(models_db.MatchResult.job_offer_id == job_id).count()
    if count > 0:
        # Mirror the Streamlit guard: refuse hard delete when evaluations exist.
        raise HTTPException(
            status_code=409,
            detail=f"This Job Offer cannot be permanently deleted because it has {count} associated evaluation(s). Set its status to CLOSED instead.",
        )
    db.delete(job)
    db.commit()
    return {"status": "deleted", "id": job_id}


# ═════════════════════════════════════════════════════════════════════════════
# CANDIDATES  (mirrors frontend/pages/candidate_history.py)
# ═════════════════════════════════════════════════════════════════════════════
class CandidateIn(BaseModel):
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Literal["NEW", "UNDER_REVIEW", "SHORTLISTED", "INTERVIEW", "HIRED", "REJECTED"] = "NEW"


def _candidate_dict(db: Session, c: models_db.Candidate) -> Dict:
    count = db.query(models_db.MatchResult).filter(models_db.MatchResult.candidate_id == c.id).count()
    best = (
        db.query(func.max(models_db.MatchResult.final_score))
        .filter(models_db.MatchResult.candidate_id == c.id)
        .scalar()
    )
    return {
        "id": c.id,
        "full_name": c.full_name,
        "email": c.email,
        "phone": c.phone,
        "status": (c.status or "NEW"),
        "is_anonymous": c.is_anonymous or 0,
        "created_at": _iso(c.created_at),
        "evaluation_count": count,
        "best_score": float(best) if best is not None else None,
    }


@router.get("/candidates")
def list_candidates(db: Session = Depends(get_db), user: models_db.User = Depends(get_current_user)) -> List[Dict]:
    cands = (
        db.query(models_db.Candidate)
        .filter(models_db.Candidate.recruiter_id == user.id)
        .order_by(models_db.Candidate.created_at.desc())
        .all()
    )
    return [_candidate_dict(db, c) for c in cands]


def _owned_candidate(db: Session, cand_id: int, user: models_db.User) -> models_db.Candidate:
    cand = (
        db.query(models_db.Candidate)
        .filter(models_db.Candidate.id == cand_id, models_db.Candidate.recruiter_id == user.id)
        .first()
    )
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    return cand


@router.put("/candidates/{cand_id}")
def update_candidate(cand_id: int, body: CandidateIn, db: Session = Depends(get_db), user: models_db.User = Depends(get_current_user)) -> Dict:
    cand = _owned_candidate(db, cand_id, user)
    if not body.full_name.strip():
        raise HTTPException(status_code=400, detail="Candidate Name is required.")
    clean_email = body.email.strip().lower() if (body.email and body.email.strip()) else None
    if clean_email and clean_email != cand.email:
        existing = db.query(models_db.Candidate).filter(models_db.Candidate.email == clean_email).first()
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot use email '{clean_email}'. It is already in use by another candidate.",
            )
    cand.full_name = body.full_name.strip()
    cand.email = clean_email
    cand.phone = (body.phone or "").strip() or None
    cand.status = body.status
    db.commit()
    db.refresh(cand)
    return _candidate_dict(db, cand)


@router.delete("/candidates/{cand_id}")
def delete_candidate(cand_id: int, db: Session = Depends(get_db), user: models_db.User = Depends(get_current_user)) -> Dict:
    cand = _owned_candidate(db, cand_id, user)
    count = db.query(models_db.MatchResult).filter(models_db.MatchResult.candidate_id == cand_id).count()
    if count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot permanently delete this candidate because they have {count} existing application(s). Change their pipeline status instead.",
        )
    db.delete(cand)
    db.commit()
    return {"status": "deleted", "id": cand_id}


# ═════════════════════════════════════════════════════════════════════════════
# ANALYSIS HISTORY  (mirrors frontend/pages/analysis_history.py)
# ═════════════════════════════════════════════════════════════════════════════
@router.get("/matches")
def list_matches(db: Session = Depends(get_db), user: models_db.User = Depends(get_current_user)) -> List[Dict]:
    matches = (
        db.query(models_db.MatchResult)
        .join(models_db.Candidate)
        .join(models_db.JobOffer)
        .filter(models_db.Candidate.recruiter_id == user.id)
        .order_by(models_db.MatchResult.created_at.desc())
        .all()
    )
    out = []
    for m in matches:
        out.append({
            "id": m.id,
            "candidate_id": m.candidate_id,
            "candidate_name": m.candidate.full_name if m.candidate else f"Unknown (ID: {m.candidate_id})",
            "candidate_email": (m.candidate.email if m.candidate and m.candidate.email else None),
            "job_offer_id": m.job_offer_id,
            "job_title": m.job_offer.title if m.job_offer else f"Unknown (ID: {m.job_offer_id})",
            "job_code": (m.job_offer.job_code if m.job_offer and m.job_offer.job_code else None),
            "final_score": m.final_score,
            "decision": m.decision,
            "confidence": m.confidence,
            "created_at": _iso(m.created_at),
        })
    return out


@router.get("/matches/{match_id}")
def match_detail(match_id: int, db: Session = Depends(get_db), user: models_db.User = Depends(get_current_user)) -> Dict:
    m = (
        db.query(models_db.MatchResult)
        .join(models_db.Candidate)
        .filter(models_db.MatchResult.id == match_id, models_db.Candidate.recruiter_id == user.id)
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Match result not found.")
    payload = json.loads(m.explanation_json) if m.explanation_json else {}
    return {
        "id": m.id,
        "candidate_name": m.candidate.full_name if m.candidate else None,
        "job_title": m.job_offer.title if m.job_offer else None,
        "final_score": m.final_score,
        "decision": m.decision,
        "created_at": _iso(m.created_at),
        "explanation": payload.get("explanation"),
        "recommendations": payload.get("recommendations"),
        "raw": payload,
    }


# ═════════════════════════════════════════════════════════════════════════════
# EVALUATE  (mirrors run_match -> evaluate_and_persist; used by Candidate
# Analysis and Talent Leaderboard)
# ═════════════════════════════════════════════════════════════════════════════
class EvaluateIn(BaseModel):
    cv_text: str
    job_offer_id: int
    model: Literal["hybrid", "embedding", "tfidf", "skill"] = "hybrid"
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    strong_fit_threshold: Optional[float] = Field(None, ge=0, le=100)
    potential_fit_threshold: Optional[float] = Field(None, ge=0, le=100)


def _run_evaluate(db: Session, user: models_db.User, cv_text: str, job_offer_id: int, model: str,
                  candidate_name: Optional[str], candidate_email: Optional[str],
                  strong: Optional[float], potential: Optional[float]) -> Dict:
    from src.matching.service import evaluate_and_persist

    if not cv_text or not cv_text.strip():
        raise HTTPException(status_code=400, detail="Please provide a CV.")
    if len(cv_text.split()) < 5:
        raise HTTPException(status_code=400, detail="Please provide more detailed CV text (minimum 5 words).")

    job = (
        db.query(models_db.JobOffer)
        .filter(models_db.JobOffer.id == job_offer_id, models_db.JobOffer.recruiter_id == user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job offer not found.")

    config = _config_from(strong, potential)
    t0 = time.perf_counter()
    payload = evaluate_and_persist(
        db, _services(), cv_text, _job_text(job),
        model_key=model,
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        job_offer_id=job_offer_id,
        recruiter_id=user.id,
        config=config,
        persist=True,
    )
    out = _serialize_payload(payload)
    out["processing_time"] = round((time.perf_counter() - t0) * 1000.0, 2)
    out["job_title"] = job.title
    return out


@router.post("/evaluate")
def evaluate(body: EvaluateIn, db: Session = Depends(get_db), user: models_db.User = Depends(get_current_user)) -> Dict:
    return _run_evaluate(
        db, user, body.cv_text, body.job_offer_id, body.model,
        body.candidate_name, body.candidate_email,
        body.strong_fit_threshold, body.potential_fit_threshold,
    )


@router.post("/evaluate/file")
async def evaluate_file(
    cv_file: UploadFile = File(...),
    job_offer_id: int = Form(...),
    model: str = Form("hybrid"),
    candidate_name: Optional[str] = Form(None),
    candidate_email: Optional[str] = Form(None),
    strong_fit_threshold: Optional[float] = Form(None),
    potential_fit_threshold: Optional[float] = Form(None),
    db: Session = Depends(get_db),
    user: models_db.User = Depends(get_current_user),
) -> Dict:
    import tempfile
    from src.parsing.parser import extract_text_from_pdf, extract_text_from_docx

    if model not in _ALLOWED_MODELS:
        raise HTTPException(status_code=400, detail=f"Unsupported model: {model}")
    suffix = Path(cv_file.filename or "").suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await cv_file.read())
        tmp_path = tmp.name
    try:
        if suffix == ".pdf":
            cv_text = extract_text_from_pdf(tmp_path)
        elif suffix in {".docx", ".doc"}:
            cv_text = extract_text_from_docx(tmp_path)
        else:
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if not cv_text or len(cv_text.split()) < 5:
        raise HTTPException(status_code=400, detail="No readable text extracted from this file.")

    return _run_evaluate(
        db, user, cv_text, job_offer_id, model,
        candidate_name, candidate_email,
        strong_fit_threshold, potential_fit_threshold,
    )


# ═════════════════════════════════════════════════════════════════════════════
# AI INSIGHTS  (mirrors frontend/pages/model_comparison.py — no persistence)
# ═════════════════════════════════════════════════════════════════════════════
class CompareIn(BaseModel):
    cv_text: str
    job_text: str


@router.post("/compare")
def compare(body: CompareIn, user: models_db.User = Depends(get_current_user)) -> Dict:
    from src.matching.service import run_evaluation

    if not body.cv_text.strip() or not body.job_text.strip():
        raise HTTPException(status_code=400, detail="Please provide both a CV and a job description.")

    models = _services()
    rows = []
    for key in ["hybrid", "embedding", "tfidf", "skill"]:
        t0 = time.perf_counter()
        try:
            payload = run_evaluation(models, body.cv_text, body.job_text, model_key=key)
            elapsed = round((time.perf_counter() - t0) * 1000.0)
            res = payload["result"]
            rows.append({
                "model": key,
                "percentage": res.get("percentage", 0.0),
                "confidence": res.get("confidence"),
                "speed_ms": elapsed,
                "decision": payload["decision"].decision,
                "band_label": payload["decision"].band_label,
            })
        except Exception as exc:  # noqa: BLE001 — mirror page's per-model error handling
            rows.append({"model": key, "percentage": 0.0, "confidence": "Error",
                         "speed_ms": None, "decision": "N/A", "band_label": "N/A", "error": str(exc)})
    return {"rows": rows}


# ═════════════════════════════════════════════════════════════════════════════
# AI QUALITY CENTER  (mirrors frontend/pages/evaluation_metrics.py — file-backed)
# ═════════════════════════════════════════════════════════════════════════════
@router.get("/quality")
def quality(user: models_db.User = Depends(get_current_user)) -> Dict:
    results_path = settings.PROJECT_ROOT / "evaluation" / "results" / "evaluation_results.json"
    if not results_path.exists():
        return {"available": False}
    try:
        payload = json.loads(results_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Failed to load evaluation results: {exc}") from exc
    mtime = datetime.fromtimestamp(results_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    n_samples = payload.get("dataset_size") or payload.get("n_samples") or payload.get("test_size")
    return {
        "available": True,
        "metrics": payload.get("metrics", {}),
        "analysis": payload.get("analysis", {}),
        "provenance": {"source": results_path.name, "generated": mtime, "n_samples": n_samples},
    }


@router.get("/quality/figures")
def quality_figures(user: models_db.User = Depends(get_current_user)) -> List[Dict]:
    figures_dir = settings.PROJECT_ROOT / "evaluation" / "figures"
    if not figures_dir.exists():
        return []
    figs = sorted(figures_dir.glob("*.png"))[:4]
    return [{"name": f.name, "label": f.stem.replace("_", " ").title()} for f in figs]


@router.get("/quality/figures/{name}")
def quality_figure(name: str, user: models_db.User = Depends(get_current_user)):
    # prevent path traversal — only a bare *.png filename inside the figures dir
    if "/" in name or "\\" in name or not name.endswith(".png"):
        raise HTTPException(status_code=400, detail="Invalid figure name.")
    path = settings.PROJECT_ROOT / "evaluation" / "figures" / name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Figure not found.")
    return FileResponse(str(path), media_type="image/png")


# ═════════════════════════════════════════════════════════════════════════════
# SETTINGS — system / model info  (mirrors frontend/pages/settings.py tabs)
# ═════════════════════════════════════════════════════════════════════════════
_MODEL_META = [
    {"key": "hybrid", "label": "Overall AI Match",
     "description": "Combines all evaluation dimensions into a single, balanced compatibility score."},
    {"key": "embedding", "label": "Semantic Relevance",
     "description": "Measures how closely the candidate's experience matches the role at a conceptual level."},
    {"key": "tfidf", "label": "Keyword Relevance",
     "description": "Analyses keyword alignment between the candidate's profile and job requirements."},
    {"key": "skill", "label": "Skills Assessment",
     "description": "Compares detected skills from the CV against the required skills in the job posting."},
]


@router.get("/system")
def system(user: models_db.User = Depends(get_current_user)) -> Dict:
    import sys
    return {
        "python_version": sys.version.split()[0],
        "models": [{**m, "status": "Active"} for m in _MODEL_META],
        "config": {
            "match_threshold": settings.MATCH_THRESHOLD,
            "embedding_model": settings.EMBEDDING_MODEL_EN,
            "rate_limit": settings.REQUEST_LIMIT_PER_MINUTE,
        },
        "defaults": {
            "strong_fit_threshold": 75.0,
            "potential_fit_threshold": 55.0,
        },
    }
