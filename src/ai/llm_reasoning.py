"""
src/ai/llm_reasoning.py

Layer 2 of NeuralHire's two-layer hybrid architecture: LLM-based *qualitative*
reasoning over the output of the (unchanged) statistical matching engine.

This module is strictly ADDITIVE and NON-BLOCKING for the core pipeline:
  * It never imports from, mutates, or is imported by the scoring/decision path.
  * Every failure mode (Ollama not installed, server down, timeout, malformed
    JSON) is caught and returned as a structured status, so the caller/UI can
    show an "AI analysis unavailable" state instead of erroring the evaluation.

Runtime: a local Ollama server (http://localhost:11434 by default) serving a
small quantized instruct model (default qwen2.5:1.5b). No training/fine-tuning —
the model reasons zero-shot using its pretrained knowledge, grounded in the
structured statistical results (see src/ai/prompts/deep_analysis_prompt.py).
"""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

import httpx

from src.config import settings
from src.ai.prompts.deep_analysis_prompt import (
    REQUIRED_KEYS,
    SYSTEM_PROMPT,
    build_user_prompt,
)

logger = logging.getLogger("jobtest.llm_reasoning")

# Status values surfaced to the API/UI. "ok" carries an analysis payload; every
# other value carries a human-readable `error` and analysis=None.
STATUS_OK = "ok"
STATUS_DISABLED = "disabled"
STATUS_UNAVAILABLE = "unavailable"
STATUS_ERROR = "error"


# ─────────────────────────────────────────────────────────────────────────────
# Context assembly — pull ONLY from already-computed results (no re-scoring)
# ─────────────────────────────────────────────────────────────────────────────
def build_context(cv_text: str, job_text: str, evaluation: Dict) -> Dict[str, object]:
    """Flatten the statistical evaluation payload into the prompt context.

    `evaluation` is the dict returned by matching.service.run_evaluation
    (keys: result, explanation, decision, ...) OR an equivalent reconstructed
    from a persisted MatchResult. All numbers here are read-only inputs to the
    prompt; the LLM is never asked to recompute them.
    """
    result = evaluation.get("result", {}) or {}
    explanation = evaluation.get("explanation", {}) or {}
    decision = evaluation.get("decision", {}) or {}
    comp = result.get("component_scores", {}) or {}
    skill_analysis = explanation.get("skill_analysis", {}) or {}
    exp_fit = explanation.get("experience_fit", {}) or {}

    # decision may be a DecisionResult-like dict or object
    def _dget(obj, key, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    return {
        "cv_text": cv_text or "",
        "job_text": job_text or "",
        "statistical": {
            "percentage": result.get("percentage"),
            "decision": _dget(decision, "decision"),
            "band_label": _dget(decision, "band_label", ""),
            "keyword": comp.get("tfidf_score"),
            "semantic": comp.get("embedding_score"),
            "skill": comp.get("skill_score"),
        },
        "skills": {
            "matched": skill_analysis.get("matching_skills", []),
            "missing": skill_analysis.get("missing_skills", []),
            "critical_missing": skill_analysis.get("critical_missing", []),
            "coverage": skill_analysis.get("skill_coverage"),
        },
        "experience": {
            "years": exp_fit.get("candidate_years"),
            "detected": exp_fit.get("candidate_years_detected"),
            "required_years": exp_fit.get("estimated_required_years"),
            "education_level": exp_fit.get("education_level"),
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Ollama availability
# ─────────────────────────────────────────────────────────────────────────────
def _envelope(status: str, *, analysis: Optional[Dict] = None, error: Optional[str] = None,
              latency_ms: Optional[float] = None) -> Dict[str, object]:
    return {
        "status": status,
        "model": settings.OLLAMA_MODEL,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "latency_ms": round(latency_ms, 1) if latency_ms is not None else None,
        "analysis": analysis,
        "error": error,
    }


def check_availability() -> Dict[str, object]:
    """Lightweight health probe. Returns {available, models, error}."""
    if not settings.LLM_ENABLED:
        return {"available": False, "models": [], "error": "LLM layer disabled (LLM_ENABLED=false)."}
    try:
        resp = httpx.get(
            f"{settings.OLLAMA_BASE_URL}/api/tags",
            timeout=settings.OLLAMA_CONNECT_TIMEOUT,
        )
        resp.raise_for_status()
        models = [m.get("name", "") for m in resp.json().get("models", [])]
        return {"available": True, "models": models, "error": None}
    except Exception as exc:  # noqa: BLE001 - any failure means "not usable"
        return {"available": False, "models": [], "error": _friendly_error(exc)}


def _friendly_error(exc: Exception) -> str:
    if isinstance(exc, (httpx.ConnectError, httpx.ConnectTimeout)):
        return ("Ollama server not reachable at "
                f"{settings.OLLAMA_BASE_URL}. Install Ollama and run `ollama serve`, "
                f"then `ollama pull {settings.OLLAMA_MODEL}`.")
    if isinstance(exc, httpx.ReadTimeout):
        return "Ollama timed out — the local model is too slow or still loading. Try again."
    return f"{type(exc).__name__}: {exc}"


# ─────────────────────────────────────────────────────────────────────────────
# JSON parsing / validation
# ─────────────────────────────────────────────────────────────────────────────
def _extract_json(raw: str) -> Optional[Dict]:
    """Parse a JSON object from the model output, tolerating stray text/fences."""
    if not raw:
        return None
    text = raw.strip()
    # strip accidental ```json fences
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # fall back to the first balanced {...} block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


def _validate(analysis: Dict) -> List[str]:
    """Return a list of schema problems (empty = valid enough to use)."""
    problems: List[str] = []
    for key in REQUIRED_KEYS:
        if key not in analysis:
            problems.append(f"missing key '{key}'")
    if "career_trajectory" in analysis and not isinstance(analysis["career_trajectory"], dict):
        problems.append("'career_trajectory' must be an object")
    for list_key in ("red_flags", "recommendations", "interview_questions"):
        if list_key in analysis and not isinstance(analysis[list_key], list):
            problems.append(f"'{list_key}' must be a list")
    if "fit_justification" in analysis and not isinstance(analysis["fit_justification"], str):
        problems.append("'fit_justification' must be a string")
    return problems


def _normalize(analysis: Dict) -> Dict:
    """Coerce to a predictable shape so the frontend can render defensively."""
    ct = analysis.get("career_trajectory") or {}
    if not isinstance(ct, dict):
        ct = {"summary": str(ct)}
    return {
        "career_trajectory": {
            "summary": str(ct.get("summary", "")).strip(),
            "seniority_signal": str(ct.get("seniority_signal", "unclear")).strip(),
            "progression": str(ct.get("progression", "")).strip(),
        },
        "red_flags": _clean_objs(analysis.get("red_flags"), ("issue", "severity", "evidence")),
        "recommendations": _clean_objs(analysis.get("recommendations"), ("recommendation", "rationale")),
        "fit_justification": str(analysis.get("fit_justification", "")).strip(),
        "interview_questions": _clean_objs(analysis.get("interview_questions"), ("question", "targets")),
    }


def _clean_objs(items, fields) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    if not isinstance(items, list):
        return out
    for item in items:
        if isinstance(item, dict):
            out.append({f: str(item.get(f, "")).strip() for f in fields})
        elif isinstance(item, str) and item.strip():
            out.append({fields[0]: item.strip()})
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Ollama call
# ─────────────────────────────────────────────────────────────────────────────
def _call_ollama(system_prompt: str, user_prompt: str) -> str:
    """One chat completion in JSON mode. Raises on transport/HTTP errors."""
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "format": "json",  # Ollama JSON-mode: constrains output to valid JSON
        # The default generation cap can truncate this five-part response on
        # very small models. 2,048 leaves enough room for every required key.
        "options": {"temperature": 0.2, "num_ctx": 8192, "num_predict": 2048},
    }
    resp = httpx.post(
        f"{settings.OLLAMA_BASE_URL}/api/chat",
        json=payload,
        timeout=httpx.Timeout(settings.OLLAMA_TIMEOUT, connect=settings.OLLAMA_CONNECT_TIMEOUT),
    )
    resp.raise_for_status()
    data = resp.json()
    return (data.get("message") or {}).get("content", "") or ""


def generate_deep_analysis(cv_text: str, job_text: str, evaluation: Dict) -> Dict[str, object]:
    """Produce the `ai_deep_analysis` envelope. NEVER raises — always returns a dict.

    Returns an envelope: {status, model, generated_at, latency_ms, analysis, error}.
    `status == "ok"` iff `analysis` is a validated deep-analysis object.
    """
    if not settings.LLM_ENABLED:
        return _envelope(STATUS_DISABLED, error="LLM layer disabled (LLM_ENABLED=false).")

    health = check_availability()
    if not health["available"]:
        return _envelope(STATUS_UNAVAILABLE, error=str(health["error"]))

    context = build_context(cv_text, job_text, evaluation)
    user_prompt = build_user_prompt(context)
    started = time.perf_counter()

    last_error = "unknown error"
    # One initial attempt + one retry on malformed/invalid JSON.
    for attempt in (1, 2):
        try:
            raw = _call_ollama(SYSTEM_PROMPT, user_prompt if attempt == 1 else _repair_hint(user_prompt))
        except Exception as exc:  # noqa: BLE001
            last_error = _friendly_error(exc)
            logger.warning("Ollama call failed (attempt %d): %s", attempt, last_error)
            # Transport errors won't be fixed by a retry with the same server.
            break

        parsed = _extract_json(raw)
        if parsed is None:
            last_error = "Model returned non-JSON output."
            logger.info("Deep analysis: unparseable output on attempt %d; %s",
                        attempt, "retrying" if attempt == 1 else "giving up")
            continue

        problems = _validate(parsed)
        if problems:
            last_error = "Malformed analysis: " + "; ".join(problems)
            logger.info("Deep analysis: schema problems on attempt %d (%s)", attempt, last_error)
            continue

        latency_ms = (time.perf_counter() - started) * 1000.0
        return _envelope(STATUS_OK, analysis=_normalize(parsed), latency_ms=latency_ms)

    latency_ms = (time.perf_counter() - started) * 1000.0
    return _envelope(STATUS_ERROR, error=last_error, latency_ms=latency_ms)


def _repair_hint(user_prompt: str) -> str:
    return (user_prompt
            + "\n\nIMPORTANT: Your previous response was not valid JSON matching the schema. "
              "Return ONLY the JSON object, with all required keys, and nothing else.")
