from __future__ import annotations

import tempfile
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List, Literal, Optional

from src.explainability.explainer import MatchingExplainer, RecommendationEngine
from src.fusion.hybrid_scorer import HybridMatcher
from src.models.embedding_model import EmbeddingMatcher
from src.models.skill_matcher import SkillMatcher
from src.models.tfidf_model import TFIDFMatcher
from src.parsing.parser import extract_text_from_docx, extract_text_from_pdf

try:
    from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, RedirectResponse
    from pydantic import BaseModel, Field
except ImportError:  # pragma: no cover - optional dependency
    FastAPI = None
    File = Form = HTTPException = Request = UploadFile = None
    CORSMiddleware = JSONResponse = RedirectResponse = None
    BaseModel = object
    Field = lambda default=None, **_: default


ALLOWED_MODELS = {"hybrid", "embedding", "tfidf", "skill"}
REQUEST_LIMIT_PER_MINUTE = 60
_REQUEST_LOG = defaultdict(deque)
_USAGE_STATS: Dict[str, float] = {
    "requests_total": 0,
    "match_requests": 0,
    "batch_requests": 0,
    "compare_requests": 0,
    "last_processing_ms": 0.0,
}


class MatchRequest(BaseModel):  # type: ignore[misc]
    cv_text: str = Field(...)
    job_text: str = Field(...)
    model: Literal["hybrid", "embedding", "tfidf", "skill"] = "hybrid"


class BatchPair(BaseModel):  # type: ignore[misc]
    cv: str
    job: str


class BatchRequest(BaseModel):  # type: ignore[misc]
    pairs: List[BatchPair]
    model: Literal["hybrid", "embedding", "tfidf", "skill"] = "hybrid"


def _build_services():
    hybrid = HybridMatcher()
    return {
        "hybrid": hybrid,
        "embedding": EmbeddingMatcher(),
        "tfidf": TFIDFMatcher(),
        "skill": SkillMatcher(),
        "explainer": MatchingExplainer(),
        "recommender": RecommendationEngine(),
    }


SERVICES = _build_services()


def _rate_limit(host: str) -> None:
    now = time.time()
    window = _REQUEST_LOG[host]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= REQUEST_LIMIT_PER_MINUTE:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please retry later.")
    window.append(now)


def _model_result(model_name: str, cv_text: str, job_text: str) -> Dict[str, object]:
    if model_name not in ALLOWED_MODELS:
        raise ValueError(f"Unsupported model: {model_name}")

    start = time.perf_counter()
    if model_name == "hybrid":
        result = SERVICES["hybrid"].predict(cv_text, job_text)
    else:
        score = float(SERVICES[model_name].predict(cv_text, job_text))
        result = {
            "final_score": round(score, 4),
            "percentage": round(score * 100.0, 1),
            "label": 1 if score >= 0.60 else 0,
            "confidence": "high" if abs(score - 0.60) > 0.15 else "medium",
            "component_scores": {f"{model_name}_score": round(score, 4)},
            "weights_used": {model_name: 1.0},
            "skill_details": SERVICES["skill"].predict_detailed(cv_text, job_text),
        }

    explanation = SERVICES["explainer"].explain(cv_text, job_text, result)
    recommendations = SERVICES["recommender"].generate(explanation["gap_analysis"])
    processing_time = round((time.perf_counter() - start) * 1000.0, 2)
    _USAGE_STATS["last_processing_ms"] = processing_time

    return {
        "score": result["final_score"],
        "percentage": result["percentage"],
        "label": result["label"],
        "confidence": result["confidence"],
        "component_scores": result.get("component_scores", {}),
        "explanation": explanation,
        "recommendations": recommendations,
        "processing_time": processing_time,
    }


def create_app():
    if FastAPI is None:  # pragma: no cover - exercised only without FastAPI
        return None

    app_instance = FastAPI(
        title="Hybrid CV Matching API",
        version="1.0.0",
        docs_url="/api/v1/docs",
        openapi_url="/api/v1/openapi.json",
    )
    app_instance.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app_instance.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/api/v1/docs")

    @app_instance.middleware("http")
    async def logging_and_rate_limit(request: Request, call_next):
        host = request.client.host if request.client else "anonymous"
        _rate_limit(host)
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000.0, 2)
        _USAGE_STATS["requests_total"] += 1
        response.headers["X-Process-Time-ms"] = str(duration_ms)
        return response

    @app_instance.get("/api/v1/health")
    async def health() -> Dict[str, object]:
        return {"status": "ok", "models": sorted(ALLOWED_MODELS), "timestamp": time.time()}

    @app_instance.get("/api/v1/metrics")
    async def metrics() -> Dict[str, object]:
        return dict(_USAGE_STATS)

    @app_instance.post("/api/v1/match")
    async def match(request: MatchRequest) -> Dict[str, object]:
        _USAGE_STATS["match_requests"] += 1
        try:
            return _model_result(request.model, request.cv_text, request.job_text)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app_instance.post("/api/v1/match/file")
    async def match_file(cv_file: UploadFile = File(...), job_text: str = Form(...), model: str = Form("hybrid")) -> Dict[str, object]:
        _USAGE_STATS["match_requests"] += 1
        suffix = Path(cv_file.filename or "").suffix.lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
            handle.write(await cv_file.read())
            temp_path = handle.name
        try:
            if suffix == ".pdf":
                cv_text = extract_text_from_pdf(temp_path)
            elif suffix == ".docx":
                cv_text = extract_text_from_docx(temp_path)
            else:
                raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")
            return _model_result(model, cv_text, job_text)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    @app_instance.post("/api/v1/batch")
    async def batch(request: BatchRequest) -> Dict[str, object]:
        _USAGE_STATS["batch_requests"] += 1
        results = [_model_result(request.model, pair.cv, pair.job) for pair in request.pairs]
        scores = [item["score"] for item in results]
        return {
            "results": results,
            "summary_stats": {
                "count": len(results),
                "mean_score": round(sum(scores) / max(1, len(scores)), 4),
                "max_score": max(scores, default=0.0),
                "min_score": min(scores, default=0.0),
            },
        }

    @app_instance.get("/api/v1/models/compare")
    async def compare_models(cv_text: str, job_text: str) -> Dict[str, object]:
        _USAGE_STATS["compare_requests"] += 1
        return {model_name: _model_result(model_name, cv_text, job_text) for model_name in sorted(ALLOWED_MODELS)}

    @app_instance.exception_handler(Exception)
    async def generic_exception_handler(_: Request, exc: Exception):
        if isinstance(exc, HTTPException):
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        return JSONResponse(status_code=500, content={"detail": str(exc)})

    return app_instance


app = create_app()
