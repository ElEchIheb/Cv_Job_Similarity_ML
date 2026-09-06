"""
src/api/main.py
JobTest AI Platform — FastAPI Backend

Endpoints:
  GET  /                          → redirect to docs
  GET  /api/v1/health             → basic health check
  GET  /api/v1/health/detailed    → model status + system info
  GET  /api/v1/metrics            → usage statistics
  POST /api/v1/match              → text-based CV matching
  POST /api/v1/match/file         → file-based CV matching (PDF/DOCX)
  POST /api/v1/batch              → batch matching (multiple pairs)
  POST /api/v1/rank               → rank multiple CVs against one job
  POST /api/v1/report/pdf         → generate PDF report from match result
  GET  /api/v1/models/compare     → compare all models on same input
"""
from __future__ import annotations

import logging
import tempfile
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List, Literal, Optional, Any

from src.config import settings
from src.explainability.explainer import MatchingExplainer, RecommendationEngine
from src.fusion.hybrid_scorer import HybridMatcher
from src.models.embedding_model import EmbeddingMatcher
from src.models.skill_matcher import SkillMatcher
from src.models.tfidf_model import TFIDFMatcher
from src.parsing.parser import extract_text_from_docx, extract_text_from_pdf

from src.logging_config import setup_logging, set_request_id

setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger("jobtest.api")

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from src.database import get_db, Base, engine
import src.models_db as models_db
from src.security.auth import get_current_user
_FASTAPI_AVAILABLE = True

# ── Constants ─────────────────────────────────────────────────────────────────
ALLOWED_MODELS   = {"hybrid", "embedding", "tfidf", "skill"}
_REQUEST_LOG: Dict[str, deque] = defaultdict(deque)
_USAGE_STATS: Dict[str, float] = {
    "requests_total":     0,
    "match_requests":     0,
    "batch_requests":     0,
    "rank_requests":      0,
    "pdf_requests":       0,
    "compare_requests":   0,
    "last_processing_ms": 0.0,
}


# ── Pydantic models ───────────────────────────────────────────────────────────
class MatchRequest(BaseModel):  # type: ignore[misc]
    """Request body for single CV–Job match."""
    cv_text:  str = Field(..., min_length=10, description="Full CV text")
    job_text: Optional[str] = Field(None, description="Full job description text")
    model:    Literal["hybrid", "embedding", "tfidf", "skill"] = Field(
        "hybrid", description="Matching model to use"
    )
    candidate_name: Optional[str] = Field(None, description="Candidate full name (for reports)")
    job_title:      Optional[str] = Field(None, description="Job title (for reports)")
    candidate_id:   Optional[int] = Field(None, description="Database candidate ID to link the match")
    job_offer_id:   int = Field(..., description="Database job offer ID to link the match")



class RankRequest(BaseModel):  # type: ignore[misc]
    """Rank multiple candidates against a single job description."""
    job_offer_id: int
    candidates: List[Dict] = Field(..., min_length=1, max_length=30,
                                   description="List of {cv_text, name} dicts")


class PDFReportRequest(BaseModel):  # type: ignore[misc]
    """Generate a PDF from pre-computed match result and explanation."""
    result:          Dict = Field(...)
    explanation:     Dict = Field(...)
    recommendations: Dict = Field(...)
    candidate_name:  Optional[str] = None
    job_title:       Optional[str] = None

class CandidateCreate(BaseModel):  # type: ignore[misc]
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None

class CandidateOut(BaseModel):  # type: ignore[misc]
    id: int
    full_name: str
    email: Optional[str]
    phone: Optional[str]

    class Config:
        from_attributes = True

class JobOfferCreate(BaseModel):  # type: ignore[misc]
    title: str
    description: str
    required_skills: Optional[str] = None

class JobOfferOut(BaseModel):  # type: ignore[misc]
    id: int
    title: str
    description: str

    class Config:
        from_attributes = True

class MatchResultOut(BaseModel):  # type: ignore[misc]
    id: int
    candidate_id: Optional[int]
    job_offer_id: Optional[int]
    final_score: Optional[float]
    confidence: Optional[str]
    decision: Optional[str]
    model_used: str
    created_at: Any

    class Config:
        from_attributes = True


# ── Service initialisation (LAZY — only runs on first request) ───────────────
import threading as _threading

_services_lock: _threading.Lock = _threading.Lock()
_services_cache: Optional[Dict] = None


def _build_services() -> Dict:
    from src.models.model_loader import load_production_models
    return load_production_models()


def _get_services() -> Dict:
    """Thread-safe lazy service getter. Models load on first call only."""
    global _services_cache
    if _services_cache is None:
        with _services_lock:
            if _services_cache is None:  # double-check after acquiring lock
                _services_cache = _build_services()
    return _services_cache


# Convenience alias for use inside route handlers
def _svc(name: str):
    return _get_services()[name]


# ── Rate limiting ─────────────────────────────────────────────────────────────
def _rate_limit(host: str) -> None:
    now    = time.time()
    window = _REQUEST_LOG[host]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= settings.REQUEST_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded ({settings.REQUEST_LIMIT_PER_MINUTE} req/min). Retry later."
        )
    window.append(now)


# ── Core matching logic ───────────────────────────────────────────────────────
def _model_result(
    model_name: str,
    cv_text: str,
    job_text: str,
) -> Dict:
    """Run a single CV–Job match and return full result with explanation."""
    if model_name not in ALLOWED_MODELS:
        raise ValueError(f"Unsupported model: {model_name!r}")

    start = time.perf_counter()

    if model_name == "hybrid":
        result = _svc("hybrid").predict(cv_text, job_text)
    else:
        score  = float(_svc(model_name).predict(cv_text, job_text))
        threshold = settings.MATCH_THRESHOLD
        result = {
            "final_score":      round(score, 4),
            "percentage":       round(score * 100.0, 1),
            "label":            1 if score >= threshold else 0,
            "confidence":       "high" if abs(score - threshold) > 0.15 else "medium",
            "component_scores": {f"{model_name}_score": round(score, 4)},
            "weights_used":     {model_name: 1.0},
            "skill_details":    _svc("skill").predict_detailed(cv_text, job_text),
        }

    explanation      = _svc("explainer").explain(cv_text, job_text, result)
    recommendations  = _svc("recommender").generate(explanation["gap_analysis"])
    processing_time  = round((time.perf_counter() - start) * 1000.0, 2)
    _USAGE_STATS["last_processing_ms"] = processing_time

    logger.info(
        "Match completed — model=%s score=%.1f%% time=%.0fms",
        model_name, result["percentage"], processing_time,
    )

    return {
        "score":             result["final_score"],
        "percentage":        result["percentage"],
        "label":             result["label"],
        "confidence":        result["confidence"],
        "component_scores":  result.get("component_scores", {}),
        "skill_details":     result.get("skill_details", {}),
        "explanation":       explanation,
        "recommendations":   recommendations,
        "processing_time":   processing_time,
    }


# ── App factory ───────────────────────────────────────────────────────────────
def create_app():
    if not _FASTAPI_AVAILABLE:  # pragma: no cover
        return None

    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized.")
    except Exception as exc:
        logger.error(f"Error initializing DB tables: {exc}")

    app_instance = FastAPI(
        title="JobTest AI Platform — API",
        description=(
            "AI-powered recruitment evaluation platform. "
            "Matches CVs to job descriptions using a hybrid NLP engine."
        ),
        version="2.0.0",
        docs_url="/api/v1/docs",
        openapi_url="/api/v1/openapi.json",
        contact={"name": "JobTest AI", "url": "https://github.com/ElEchIheb"},
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    from src.api.routers.auth import router as auth_router
    app_instance.include_router(auth_router)

    # Additive UI-parity router (wraps existing service/DB logic for the
    # Next.js frontend; no algorithm/threshold/schema changes).
    from src.api.routers.ui import router as ui_router
    app_instance.include_router(ui_router)

    # ── CORS ──────────────────────────────────────────────────────────────────
    app_instance.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
    )

    # ── Middleware: logging + timing + rate limiting ───────────────────────────
    @app_instance.middleware("http")
    async def request_middleware(request: Request, call_next):
        req_id = set_request_id()
        host  = request.client.host if request.client else "anonymous"
        start = time.perf_counter()
        try:
            _rate_limit(host)
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.exception("Unhandled exception during request processing")
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error. Check logs for details."}
            )

        duration_ms = round((time.perf_counter() - start) * 1000.0, 2)
        _USAGE_STATS["requests_total"] += 1
        response.headers["X-Process-Time-ms"] = str(duration_ms)
        response.headers["X-Request-ID"] = req_id
        logger.debug("%s %s → %d (%.0fms)", request.method, request.url.path,
                     response.status_code, duration_ms)
        return response

    # ── Routes ────────────────────────────────────────────────────────────────
    @app_instance.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/api/v1/docs")

    @app_instance.get("/api/v1/health", tags=["System"])
    async def health() -> Dict:
        """Basic liveness check."""
        return {
            "status":    "ok",
            "version":   "2.0.0",
            "models":    sorted(ALLOWED_MODELS),
            "timestamp": time.time(),
        }

    @app_instance.get("/api/v1/health/detailed", tags=["System"])
    async def health_detailed() -> Dict:
        """Extended health check with model status."""
        model_status = {}
        for name in ALLOWED_MODELS:
            try:
                _ = _svc(name).predict("python developer", "python developer")
                model_status[name] = "ok"
            except Exception as exc:
                model_status[name] = f"error: {exc}"
        return {
            "status":       "ok" if all(v == "ok" for v in model_status.values()) else "degraded",
            "model_status": model_status,
            "config": {
                "match_threshold":  settings.MATCH_THRESHOLD,
                "embedding_model":  settings.EMBEDDING_MODEL_EN,
                "rate_limit":       settings.REQUEST_LIMIT_PER_MINUTE,
            },
            "usage":     dict(_USAGE_STATS),
            "timestamp": time.time(),
        }

    @app_instance.get("/api/v1/metrics", tags=["System"])
    async def metrics() -> Dict:
        """Usage statistics."""
        return dict(_USAGE_STATS)

    @app_instance.post("/api/v1/candidates", response_model=CandidateOut, tags=["Database"])
    def create_candidate(candidate: CandidateCreate, db: Session = Depends(get_db), current_user: models_db.User = Depends(get_current_user)):
        """Create a new candidate in the database."""
        db_cand = models_db.Candidate(**candidate.model_dump(), recruiter_id=current_user.id)
        db.add(db_cand)
        db.commit()
        db.refresh(db_cand)
        return db_cand

    @app_instance.get("/api/v1/candidates", response_model=List[CandidateOut], tags=["Database"])
    def read_candidates(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models_db.User = Depends(get_current_user)):
        """Retrieve candidates from the database."""
        candidates = db.query(models_db.Candidate).filter(models_db.Candidate.recruiter_id == current_user.id).offset(skip).limit(limit).all()
        return candidates

    @app_instance.post("/api/v1/job-offers", response_model=JobOfferOut, tags=["Database"])
    def create_job_offer(offer: JobOfferCreate, db: Session = Depends(get_db), current_user: models_db.User = Depends(get_current_user)):
        """Create a new job offer in the database."""
        offer_data = offer.model_dump()
        if "required_skills" in offer_data:
            offer_data["required_skills_raw"] = offer_data.pop("required_skills")
            
        db_offer = models_db.JobOffer(**offer_data, recruiter_id=current_user.id)
        db.add(db_offer)
        db.commit()
        db.refresh(db_offer)
        return db_offer

    @app_instance.get("/api/v1/job-offers", response_model=List[JobOfferOut], tags=["Database"])
    def read_job_offers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models_db.User = Depends(get_current_user)):
        """Retrieve job offers from the database."""
        offers = db.query(models_db.JobOffer).filter(models_db.JobOffer.recruiter_id == current_user.id).offset(skip).limit(limit).all()
        return offers

    @app_instance.post("/api/v1/match", tags=["Matching"])
    async def match(request: MatchRequest, db: Session = Depends(get_db), current_user: models_db.User = Depends(get_current_user)) -> Dict:
        """Match a single CV against a job description and save to database."""
        _USAGE_STATS["match_requests"] += 1
        try:
            job_text = request.job_text
            if not job_text:
                job = db.query(models_db.JobOffer).filter(models_db.JobOffer.id == request.job_offer_id).first()
                if not job:
                    raise HTTPException(status_code=404, detail="Job offer not found")
                job_text = f"{job.title}\n\n{job.description}\n\nRequired Skills: {job.required_skills_raw}"

            result = _model_result(request.model, request.cv_text, job_text)
            
            # Save MatchResult if candidate and job offer are provided
            if request.candidate_id and request.job_offer_id:
                import json
                db_result = models_db.MatchResult(
                    candidate_id=request.candidate_id,
                    job_offer_id=request.job_offer_id,
                    final_score=result.get("score"),
                    score_hybrid=result.get("component_scores", {}).get("hybrid_score"),
                    score_semantic=result.get("component_scores", {}).get("embedding_score"),
                    score_keyword=result.get("component_scores", {}).get("tfidf_score"),
                    score_skill=result.get("component_scores", {}).get("skill_score"),
                    confidence=result.get("explanation", {}).get("hiring_recommendation", {}).get("confidence_level"),
                    decision=result.get("explanation", {}).get("hiring_recommendation", {}).get("decision", "CONSIDER"),
                    decision_confidence=result.get("explanation", {}).get("hiring_recommendation", {}).get("confidence"),
                    strong_fit_threshold=result.get("explanation", {}).get("decision_config", {}).get("strong_fit_threshold"),
                    potential_fit_threshold=result.get("explanation", {}).get("decision_config", {}).get("potential_fit_threshold"),
                    model_version="hybrid-checkpoint-v2",
                    model_used=request.model,
                    decision_config=json.dumps(result.get("explanation", {}).get("decision_config", {})),
                    metadata_flags=json.dumps({
                        "model": request.model,
                        "time": processing_time
                    }),
                    explanation_json=json.dumps({
                        "explanation": result.get("explanation"),
                        "recommendations": result.get("recommendations")
                    })
                )
                db.add(db_result)
                db.commit()
                db.refresh(db_result)
                result["match_id"] = db_result.id
                result["job_offer_id"] = request.job_offer_id
                result["decision"] = db_result.decision
            
            # For backward compatibility if not persisting but we have a decision
            if "decision" not in result:
                result["decision"] = result.get("explanation", {}).get("hiring_recommendation", {}).get("decision", "CONSIDER")
            result["final_score"] = result.get("score")
            if request.job_offer_id:
                result["job_offer_id"] = request.job_offer_id

            return result
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app_instance.get("/api/v1/matches", tags=["Database"])
    def read_matches(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models_db.User = Depends(get_current_user)):
        """Retrieve match history from the database."""
        matches = db.query(models_db.MatchResult).join(models_db.Candidate).filter(models_db.Candidate.recruiter_id == current_user.id).offset(skip).limit(limit).all()
        # Return a simple dict list for now
        return [
            {
                "id": m.id,
                "candidate_id": m.candidate_id,
                "job_offer_id": m.job_offer_id,
                "final_score": m.final_score,
                "confidence": m.confidence,
                "decision": m.decision,
                "created_at": m.created_at.isoformat() if m.created_at else None
            }
            for m in matches
        ]

    @app_instance.get("/api/v1/matches/{match_id}", tags=["Database"])
    def get_match(match_id: int, db: Session = Depends(get_db), current_user: models_db.User = Depends(get_current_user)):
        """Retrieve full details of a specific match result."""
        match = db.query(models_db.MatchResult).join(models_db.Candidate).filter(models_db.MatchResult.id == match_id, models_db.Candidate.recruiter_id == current_user.id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Match result not found")
        
        import json
        return {
            "id": match.id,
            "candidate_id": match.candidate_id,
            "job_offer_id": match.job_offer_id,
            "final_score": match.final_score,
            "confidence": match.confidence,
            "decision": match.decision,
            "explanation": json.loads(match.explanation_json) if match.explanation_json else None
        }

    @app_instance.post("/api/v1/match/file", tags=["Matching"])
    async def match_file(
        cv_file:  UploadFile = File(...),
        job_text: str        = Form(...),
        model:    str        = Form("hybrid"),
        candidate_id: Optional[int] = Form(None),
        job_offer_id: Optional[int] = Form(None),
        db: Session = Depends(get_db),
        current_user: models_db.User = Depends(get_current_user)
    ) -> Dict:
        """Match a CV file (PDF or DOCX) against a job description."""
        _USAGE_STATS["match_requests"] += 1
        suffix = Path(cv_file.filename or "").suffix.lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
            handle.write(await cv_file.read())
            temp_path = handle.name
        try:
            if suffix == ".pdf":
                cv_text = extract_text_from_pdf(temp_path)
            elif suffix in {".docx", ".doc"}:
                cv_text = extract_text_from_docx(temp_path)
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Only PDF and DOCX files are supported.",
                )
            
            result = _model_result(model, cv_text, job_text)
            
            # Save MatchResult if candidate and job offer are provided
            if candidate_id and job_offer_id:
                import json
                db_result = models_db.MatchResult(
                    candidate_id=candidate_id,
                    job_offer_id=job_offer_id,
                    final_score=result.get("score"),
                    score_hybrid=result.get("component_scores", {}).get("hybrid_score"),
                    score_semantic=result.get("component_scores", {}).get("embedding_score"),
                    score_keyword=result.get("component_scores", {}).get("tfidf_score"),
                    score_skill=result.get("component_scores", {}).get("skill_score"),
                    confidence=result.get("explanation", {}).get("hiring_recommendation", {}).get("confidence_level"),
                    decision=result.get("explanation", {}).get("hiring_recommendation", {}).get("decision", "CONSIDER"),
                    decision_confidence=result.get("explanation", {}).get("hiring_recommendation", {}).get("confidence"),
                    strong_fit_threshold=result.get("explanation", {}).get("decision_config", {}).get("strong_fit_threshold"),
                    potential_fit_threshold=result.get("explanation", {}).get("decision_config", {}).get("potential_fit_threshold"),
                    model_version="hybrid-checkpoint-v2",
                    model_used=model,
                    explanation_json=json.dumps({
                        "explanation": result.get("explanation"),
                        "recommendations": result.get("recommendations")
                    })
                )
                db.add(db_result)
                db.commit()
                db.refresh(db_result)
                result["match_id"] = db_result.id
            
            return result
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Error processing file upload")
            raise HTTPException(status_code=500, detail=f"File processing error: {exc}") from exc
        finally:
            Path(temp_path).unlink(missing_ok=True)



    @app_instance.post("/api/v1/rank", tags=["Ranking"])
    async def rank_candidates(request: RankRequest, db: Session = Depends(get_db), current_user: models_db.User = Depends(get_current_user)) -> Dict:
        """
        Rank multiple candidates against a single job description.
        Returns candidates sorted by match score (best first).
        """
        _USAGE_STATS["rank_requests"] += 1
        
        job = db.query(models_db.JobOffer).filter(models_db.JobOffer.id == request.job_offer_id).first()
        if not job:
            raise HTTPException(status_code=404, detail=f"JobOffer {request.job_offer_id} not found.")
            
        job_text = f"{job.title}\n\n{job.description}\n\nRequired Skills: {job.required_skills_raw}"
        
        logger.info("Ranking %d candidates for job: %s",
                    len(request.candidates), job.title)
        ranked = []
        for candidate in request.candidates:
            cv_text = candidate.get("cv_text", "")
            name    = candidate.get("name", "Unknown")
            if not cv_text:
                continue
            try:
                res = _model_result("hybrid", cv_text, job_text)
                ranked.append({
                    "rank":              0,  # filled below
                    "candidate_name":    name,
                    "score":             res["score"],
                    "percentage":        res["percentage"],
                    "label":             res["label"],
                    "confidence":        res["confidence"],
                    "decision":          res["explanation"].get("hiring_recommendation", {}).get("decision", "N/A"),
                    "matched_skills":    res["explanation"].get("skill_analysis", {}).get("matching_skills", [])[:5],
                    "critical_missing":  res["explanation"].get("skill_analysis", {}).get("critical_missing", [])[:3],
                    "strengths":         res["explanation"].get("gap_analysis", {}).get("strengths", [])[:2],
                    "full_result":       res,
                })
            except Exception as exc:
                logger.warning("Failed to rank candidate '%s': %s", name, exc)
                ranked.append({"candidate_name": name, "error": str(exc)})

        ranked.sort(key=lambda x: x.get("score", -1), reverse=True)
        for i, item in enumerate(ranked, 1):
            item["rank"] = i

        return {
            "job_title":    job.title,
            "total_ranked": len(ranked),
            "ranked":       ranked,
        }

    @app_instance.post("/api/v1/report/pdf", tags=["Reports"])
    async def generate_pdf_report(request: PDFReportRequest, current_user: models_db.User = Depends(get_current_user)):
        """Generate a professional PDF evaluation report."""
        _USAGE_STATS["pdf_requests"] += 1
        try:
            from src.reporting.pdf_generator import MatchReportPDF
            generator  = MatchReportPDF()
            pdf_bytes  = generator.generate(
                result          = request.result,
                explanation     = request.explanation,
                recommendations = request.recommendations,
                candidate_name  = request.candidate_name or "Candidate",
                job_title       = request.job_title or "Position",
            )
            return Response(
                content      = pdf_bytes,
                media_type   = "application/pdf",
                headers      = {
                    "Content-Disposition": (
                        f'attachment; filename="evaluation_{request.candidate_name or "report"}.pdf"'
                    )
                },
            )
        except ImportError:
            raise HTTPException(
                status_code=501,
                detail="PDF generation requires reportlab. Run: pip install reportlab",
            )
        except Exception as exc:
            logger.exception("PDF generation failed")
            raise HTTPException(status_code=500, detail=f"PDF generation error: {exc}") from exc

    @app_instance.get("/api/v1/models/compare", tags=["Matching"])
    async def compare_models(cv_text: str, job_text: str, current_user: models_db.User = Depends(get_current_user)) -> Dict:
        """Compare all models on the same CV–job pair."""
        _USAGE_STATS["compare_requests"] += 1
        return {
            model_name: _model_result(model_name, cv_text, job_text)
            for model_name in sorted(ALLOWED_MODELS)
        }


    @app_instance.delete("/api/v1/candidates/{candidate_id}", tags=["GDPR"])
    def delete_candidate(candidate_id: int, db: Session = Depends(get_db), current_user: models_db.User = Depends(get_current_user)):
        """Hard delete a candidate and cascade delete matches/CVs."""
        cand = db.query(models_db.Candidate).filter(models_db.Candidate.id == candidate_id, models_db.Candidate.recruiter_id == current_user.id).first()
        if not cand:
            raise HTTPException(status_code=404, detail="Candidate not found")
        db.delete(cand)
        db.commit()
        return {"status": "deleted"}

    @app_instance.post("/api/v1/candidates/{candidate_id}/anonymize", tags=["GDPR"])
    def anonymize_candidate(candidate_id: int, db: Session = Depends(get_db), current_user: models_db.User = Depends(get_current_user)):
        """Anonymize a candidate to preserve match analytics without PII."""
        cand = db.query(models_db.Candidate).filter(models_db.Candidate.id == candidate_id, models_db.Candidate.recruiter_id == current_user.id).first()
        if not cand:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        cand.full_name = f"Candidate #{cand.id}"
        cand.email = None
        cand.phone = None
        db.commit()
        return {"status": "anonymized"}

    # ── Exception handlers ────────────────────────────────────────────────────
    @app_instance.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "status_code": exc.status_code},
        )

    @app_instance.exception_handler(Exception)
    async def generic_exception_handler(_: Request, exc: Exception):
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error. Check logs for details."},
        )

    return app_instance


app = create_app()

# touch