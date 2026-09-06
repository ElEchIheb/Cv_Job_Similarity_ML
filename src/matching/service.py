"""
src/matching/service.py
Canonical evaluation + persistence service for NeuralHire.

This is the ONE place that:
  1. runs the AI models for a CV/Job pair,
  2. derives the recruiter decision via the central DecisionEngine,
  3. injects that single decision into the explanation, and
  4. persists a fully-described, reproducible evaluation with de-duplicated
     Candidate and Job entities.

Every UI surface (Candidate Analysis, Talent Leaderboard, Bulk Evaluation)
routes through `run_evaluation` / `evaluate_and_persist`, guaranteeing that the
same (candidate, job, configuration) yields the same decision everywhere.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy import func

from src import models_db
from src.decisioning import DecisionConfig, DecisionEngine, DEFAULT_STRONG_FIT, DEFAULT_POTENTIAL_FIT

logger = logging.getLogger("jobtest.matching")

MODEL_VERSION = "hybrid-checkpoint-v2"

_GENERIC_CANDIDATE = {"", "anonymous candidate", "anonymous", "unknown", "unknown candidate"}
_GENERIC_JOB = {"", "unnamed job offer", "untitled", "n/a"}


# ─────────────────────────────────────────────────────────────────────────────
# EVALUATION (pure — no DB)
# ─────────────────────────────────────────────────────────────────────────────

def run_evaluation(models: Dict, cv_text: str, job_text: str,
                   model_key: str = "hybrid",
                   config: Optional[DecisionConfig] = None) -> Dict:
    """Run the AI evaluation and attach the ONE canonical decision.

    `models` is the loaded services dict (hybrid/embedding/tfidf/skill/
    explainer/recommender). Returns {result, explanation, recommendations,
    decision, config}.
    """
    config = config or DecisionConfig.default()
    engine = DecisionEngine(config)

    if model_key == "hybrid":
        result = models["hybrid"].predict(cv_text, job_text)
    else:
        raw = float(models[model_key].predict(cv_text, job_text))
        result = {
            "final_score": round(raw, 4),
            "percentage": round(raw * 100.0, 1),
            "confidence": None,
            "component_scores": {f"{model_key}_score": round(raw, 4)},
            "weights_used": {model_key: 1.0},
            "skill_details": models["skill"].predict_detailed(cv_text, job_text),
        }

    pct = float(result.get("percentage", 0.0))
    skill_details = result.get("skill_details", {})
    critical_missing = list(skill_details.get("critical_missing", []))

    # ── The single source of truth for the decision ────────────────────────
    # Both the DecisionResult used for persistence and the explanation's
    # hiring_recommendation are produced by the SAME DecisionEngine + config,
    # so they can never disagree.
    decision = engine.evaluate(pct, config, critical_missing=critical_missing)
    explanation = models["explainer"].explain(cv_text, job_text, result, config=config)

    return {
        "result": result,
        "explanation": explanation,
        "recommendations": models["recommender"].generate(explanation["gap_analysis"]),
        "decision": decision,
        "config": config,
        "model_key": model_key,
    }


def _verdict_text(decision: str) -> str:
    return {"HIRE": "Strong Match", "CONSIDER": "Potential Match",
            "REJECT": "Weak Match"}.get(decision, "Potential Match")


# ─────────────────────────────────────────────────────────────────────────────
# PERSISTENCE (with de-duplication)
# ─────────────────────────────────────────────────────────────────────────────

def _next_anonymous_label(db, recruiter_id: Optional[int]) -> str:
    year = datetime.utcnow().year
    q = db.query(models_db.Candidate).filter(models_db.Candidate.is_anonymous == 1)
    if recruiter_id is not None:
        q = q.filter(models_db.Candidate.recruiter_id == recruiter_id)
    seq = q.count() + 1
    # guarantee uniqueness even across years / races
    label = f"Candidate #{year}-{seq:03d}"
    while db.query(models_db.Candidate).filter(models_db.Candidate.full_name == label).first():
        seq += 1
        label = f"Candidate #{year}-{seq:03d}"
    return label


def _resolve_candidate(db, name: Optional[str], email: Optional[str], recruiter_id: Optional[int]):
    """Reuse an existing candidate by email, or create one (stable label if anon)."""
    clean_name = (name or "").strip()
    clean_email = (email or "").strip().lower()
    
    if clean_email:
        existing = (
            db.query(models_db.Candidate)
            .filter(models_db.Candidate.recruiter_id == recruiter_id)
            .filter(func.lower(models_db.Candidate.email) == clean_email)
            .first()
        )
        if existing:
            return existing, False
            
        cand_name = clean_name if (clean_name and clean_name.lower() not in _GENERIC_CANDIDATE) else "Candidate (No Name)"
        cand = models_db.Candidate(full_name=cand_name, email=clean_email, recruiter_id=recruiter_id,
                                   status="NEW", is_anonymous=0)
    elif clean_name and clean_name.lower() not in _GENERIC_CANDIDATE:
        cand = models_db.Candidate(full_name=clean_name, recruiter_id=recruiter_id,
                                   status="NEW", is_anonymous=0)
    else:
        cand = models_db.Candidate(full_name=_next_anonymous_label(db, recruiter_id),
                                   recruiter_id=recruiter_id, status="NEW", is_anonymous=1)
    db.add(cand)
    db.flush()
    return cand, True


def persist_evaluation(db, payload: Dict, cv_text: str,
                       candidate_name: Optional[str], candidate_email: Optional[str],
                       job_offer_id: int, recruiter_id: Optional[int]) -> models_db.MatchResult:
    """Persist a completed evaluation atomically with de-duplicated entities."""
    result = payload["result"]
    explanation = payload["explanation"]
    recommendations = payload["recommendations"]
    decision = payload["decision"]
    config = payload["config"]
    model_key = payload.get("model_key", "hybrid")

    comp = result.get("component_scores", {})
    
    job = db.query(models_db.JobOffer).filter(models_db.JobOffer.id == job_offer_id).first()
    if not job:
        raise ValueError(f"JobOffer with id {job_offer_id} not found.")

    candidate, _ = _resolve_candidate(db, candidate_name, candidate_email, recruiter_id)

    # Persist the CV document reference
    cv_row = models_db.CV(candidate_id=candidate.id, filename=None, content_text=cv_text or "")
    db.add(cv_row)
    db.flush()

    match = models_db.MatchResult(
        candidate_id=candidate.id,
        cv_id=cv_row.id,
        job_offer_id=job.id,
        final_score=result.get("final_score"),
        score_hybrid=result.get("final_score") if model_key == "hybrid" else None,
        score_semantic=comp.get("embedding_score"),
        score_keyword=comp.get("tfidf_score"),
        score_skill=comp.get("skill_score"),
        confidence=decision.confidence_level,
        decision=decision.decision,
        decision_confidence=decision.confidence,
        strong_fit_threshold=config.strong_fit_threshold,
        potential_fit_threshold=config.potential_fit_threshold,
        model_version=MODEL_VERSION,
        evaluation_method=model_key,
        weights_json=json.dumps(result.get("weights_used", {})),
        model_used=model_key,
        explanation_json=json.dumps({
            "explanation": explanation,
            "recommendations": recommendations,
        }),
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


def evaluate_and_persist(db, models: Dict, cv_text: str, job_text: str,
                         model_key: str = "hybrid",
                         candidate_name: Optional[str] = None,
                         candidate_email: Optional[str] = None,
                         job_offer_id: Optional[int] = None,
                         recruiter_id: Optional[int] = None,
                         config: Optional[DecisionConfig] = None,
                         persist: bool = True) -> Dict:
    """Full canonical flow used by the frontend. Returns the UI payload."""
    if persist and not job_offer_id:
        raise ValueError("job_offer_id is required to persist evaluation.")
        
    payload = run_evaluation(models, cv_text, job_text, model_key, config)
    if persist:
        try:
            match = persist_evaluation(db, payload, cv_text,
                                       candidate_name, candidate_email, job_offer_id, recruiter_id)
            payload["match_id"] = match.id
        except Exception:
            logger.exception("Failed to persist evaluation")
            db.rollback()
            raise
    return payload
