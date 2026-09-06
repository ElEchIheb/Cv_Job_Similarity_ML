"""Tests for Layer 2 (LLM reasoning) that do NOT require a running Ollama.

They cover the parsing/validation/normalisation logic, prompt grounding, and the
graceful-degradation contract. The one 'happy path' test mocks the Ollama call so
no server is needed.
"""
from __future__ import annotations

import json

import pytest

from src.ai import llm_reasoning as L
from src.ai.prompts.deep_analysis_prompt import build_user_prompt, REQUIRED_KEYS


# ── fixtures ──────────────────────────────────────────────────────────────────
def _evaluation():
    return {
        "result": {"percentage": 88.0,
                   "component_scores": {"tfidf_score": 0.9, "embedding_score": 0.8, "skill_score": 1.0}},
        "explanation": {
            "skill_analysis": {"matching_skills": ["react", "sql"], "missing_skills": [],
                               "critical_missing": [], "skill_coverage": "11/11 required skills"},
            "experience_fit": {"candidate_years": 3.0, "candidate_years_detected": True,
                               "estimated_required_years": 3.0, "education_level": "Bachelor"},
        },
        "decision": {"decision": "HIRE", "band_label": "Strong Fit"},
    }


def _valid_analysis():
    return {
        "career_trajectory": {"summary": "s", "seniority_signal": "mid-level", "progression": "p"},
        "red_flags": [{"issue": "gap", "severity": "low", "evidence": "e"}],
        "recommendations": [{"recommendation": "r", "rationale": "why"}],
        "fit_justification": "Solid fit.",
        "interview_questions": [{"question": "q?", "targets": "skill"}],
    }


# ── context + prompt grounding ────────────────────────────────────────────────
def test_build_context_pulls_statistical_fields():
    ctx = L.build_context("CV", "JOB", _evaluation())
    assert ctx["statistical"]["percentage"] == 88.0
    assert ctx["statistical"]["decision"] == "HIRE"
    assert ctx["skills"]["coverage"] == "11/11 required skills"
    assert ctx["experience"]["years"] == 3.0


def test_prompt_is_grounded_in_numbers():
    up = build_user_prompt(L.build_context("my cv text", "my job text", _evaluation()))
    assert "88.0%" in up
    assert "HIRE" in up
    assert "11/11 required skills" in up
    # every required output key is described in the schema block
    for key in REQUIRED_KEYS:
        assert key in up


# ── JSON extraction tolerance ─────────────────────────────────────────────────
def test_extract_json_plain():
    assert L._extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_fenced():
    assert L._extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_with_surrounding_text():
    assert L._extract_json('Here is the result: {"a": 1} thanks') == {"a": 1}


def test_extract_json_garbage_returns_none():
    assert L._extract_json("not json at all") is None


# ── validation + normalisation ────────────────────────────────────────────────
def test_validate_accepts_full_object():
    assert L._validate(_valid_analysis()) == []


def test_validate_flags_missing_key():
    bad = _valid_analysis()
    del bad["fit_justification"]
    problems = L._validate(bad)
    assert any("fit_justification" in p for p in problems)


def test_normalize_coerces_shapes():
    messy = {
        "career_trajectory": "just a string",
        "red_flags": ["plain string flag"],
        "recommendations": [{"recommendation": "do x"}],
        "fit_justification": 123,
        "interview_questions": [],
    }
    norm = L._normalize(messy)
    assert isinstance(norm["career_trajectory"], dict)
    assert norm["red_flags"][0]["issue"] == "plain string flag"
    assert norm["recommendations"][0]["recommendation"] == "do x"
    assert isinstance(norm["fit_justification"], str)


# ── graceful degradation contract ─────────────────────────────────────────────
def test_disabled_returns_disabled_status(monkeypatch):
    monkeypatch.setattr(L.settings, "LLM_ENABLED", False)
    env = L.generate_deep_analysis("cv", "job", _evaluation())
    assert env["status"] == L.STATUS_DISABLED
    assert env["analysis"] is None


def test_unavailable_when_server_down(monkeypatch):
    monkeypatch.setattr(L.settings, "LLM_ENABLED", True)
    monkeypatch.setattr(L, "check_availability",
                        lambda: {"available": False, "models": [], "error": "down"})
    env = L.generate_deep_analysis("cv", "job", _evaluation())
    assert env["status"] == L.STATUS_UNAVAILABLE
    assert env["analysis"] is None
    assert env["error"] == "down"


def test_happy_path_with_mocked_ollama(monkeypatch):
    monkeypatch.setattr(L.settings, "LLM_ENABLED", True)
    monkeypatch.setattr(L, "check_availability",
                        lambda: {"available": True, "models": ["llama3.2:3b"], "error": None})
    monkeypatch.setattr(L, "_call_ollama", lambda sys, usr: json.dumps(_valid_analysis()))
    env = L.generate_deep_analysis("cv", "job", _evaluation())
    assert env["status"] == L.STATUS_OK
    assert env["analysis"]["career_trajectory"]["seniority_signal"] == "mid-level"
    assert env["analysis"]["interview_questions"][0]["question"] == "q?"
    assert env["latency_ms"] is not None


def test_retry_then_fail_on_malformed(monkeypatch):
    monkeypatch.setattr(L.settings, "LLM_ENABLED", True)
    monkeypatch.setattr(L, "check_availability",
                        lambda: {"available": True, "models": ["m"], "error": None})
    monkeypatch.setattr(L, "_call_ollama", lambda sys, usr: "still not json")
    env = L.generate_deep_analysis("cv", "job", _evaluation())
    assert env["status"] == L.STATUS_ERROR
    assert env["analysis"] is None
