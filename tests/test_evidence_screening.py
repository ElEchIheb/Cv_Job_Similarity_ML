"""
Regression tests for the evidence screening (copied offer text, negations,
declared vs demonstrated skills) and the HIRE evidence rule.
"""
from __future__ import annotations

import pytest

from src.decisioning import DecisionEngine, CONSIDER, HIRE, REJECT
from src.nlp.screening import (
    evidence_insufficient, remove_copied_spans, screen_cv, split_declared_evidence, strip_negated,
)

JOB = ("Senior Data Engineer. Required: python, sql, apache airflow, apache spark, docker, kubernetes. "
       "Nice to have: kafka, aws. Strong communication skills.")
UNRELATED = ("PROFILE\nGraphic designer with 6 years of experience.\n\nEXPERIENCE\n"
             "2019-2025 Designer: brand identities, print layouts and packaging.\n\n"
             "SKILLS\nphotoshop, illustrator, indesign, typography")
GENUINE = ("PROFILE\nData engineer with 5 years of experience.\n\nEXPERIENCE\n"
           "2021-2026: built batch pipelines in Python and SQL, orchestrated with Apache Airflow, "
           "processed data with Apache Spark, deployed with Docker on Kubernetes.\n\n"
           "SKILLS\nPython, SQL, Airflow, Spark, Docker, Kubernetes")


# ── Copied offer text ────────────────────────────────────────────────────────
def test_verbatim_requirement_list_is_removed():
    stuffed = UNRELATED + "\n\nRequired: python, sql, apache airflow, apache spark, docker, kubernetes."
    cleaned, copied, spans = remove_copied_spans(stuffed, JOB)
    assert copied >= 8 and spans == 1
    assert "airflow" not in cleaned.lower()
    assert "graphic designer" in cleaned.lower()


def test_genuine_cv_is_not_altered():
    cleaned, copied, _ = remove_copied_spans(GENUINE, JOB)
    assert copied == 0 and cleaned == GENUINE


def test_short_common_phrases_are_kept():
    cv = "Data engineer with strong communication skills and python experience."
    assert remove_copied_spans(cv, JOB)[1] == 0


# ── Negations ────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("text", [
    "No experience with Kubernetes.",
    "I have never used kubernetes in production.",
    "Sans expérience sur Kubernetes.",
    "Je n'ai aucune expérience en Kubernetes.",
    "Je ne maîtrise pas Kubernetes.",
])
def test_negated_mentions_are_dropped(text):
    assert "kubernetes" not in strip_negated(text).lower()


def test_negation_covers_dotted_skill_names():
    out = strip_negated("No experience with node.js, next.js and react. Daily use of Docker.").lower()
    assert "node.js" not in out and "react" not in out and "docker" in out


def test_negation_is_local_to_its_clause():
    out = strip_negated("No experience with Kubernetes. Daily use of Docker.").lower()
    assert "kubernetes" not in out and "docker" in out


# ── Declared vs demonstrated ────────────────────────────────────────────────
def test_sections_split_declared_and_evidence():
    declared, evidence, structured = split_declared_evidence(UNRELATED)
    assert structured
    assert "photoshop" in declared and "photoshop" not in evidence
    assert "brand identities" in evidence


def test_inline_skills_line_is_declared():
    declared, evidence, structured = split_declared_evidence("EXPERIENCE\nDesigner 2020-2024\nSkills: python, sql")
    assert structured and "python" in declared and "python" not in evidence


def test_certifications_count_as_evidence():
    _, evidence, _ = split_declared_evidence("SKILLS\naws\n\nCERTIFICATIONS\nAWS Certified Solutions Architect")
    assert "aws certified" in evidence.lower()


def test_unstructured_cv_counts_everything_as_evidence():
    declared, evidence, structured = split_declared_evidence("Data engineer, python sql airflow spark")
    assert not structured and declared == "" and "python" in evidence


# ── Skill component and HIRE rule ───────────────────────────────────────────
@pytest.fixture(scope="module")
def matcher():
    from src.models.skill_matcher import SkillMatcher
    return SkillMatcher()


def test_declared_only_skills_count_for_less(matcher):
    stuffed = UNRELATED + "\n\nSKILLS\nsql, docker, python, kubernetes, apache spark, apache airflow"
    genuine = matcher.predict_detailed(GENUINE, JOB)
    listed = matcher.predict_detailed(stuffed, JOB)
    assert listed["evidence"]["demonstrated_count"] == 0
    assert listed["evidence"]["declared_only_skills"]
    assert listed["hard_score"] < genuine["hard_score"]
    assert evidence_insufficient(listed)[0]
    assert not evidence_insufficient(genuine)[0]


def test_negated_skills_are_not_matched(matcher):
    cv = UNRELATED + "\n\nEXPERIENCE\nNo professional experience with python, sql, docker or kubernetes."
    details = matcher.predict_detailed(cv, JOB)
    assert not ({"python", "sql", "docker", "kubernetes"} & set(details["matching_hard_skills"]))


def test_copied_offer_triggers_the_evidence_rule(matcher):
    cv = GENUINE + "\n\n" + JOB
    assert evidence_insufficient(matcher.predict_detailed(cv, JOB)) == (True, "part of the CV repeats the offer verbatim")


def test_engine_withholds_hire_only():
    engine = DecisionEngine()
    capped = engine.evaluate(90, evidence_gap="only 0 of 5 matched skills are supported by the described experience")
    assert capped.decision == CONSIDER and capped.percentage == 90
    assert "verify the experience" in capped.reason
    assert engine.evaluate(60, evidence_gap="x").decision == CONSIDER
    assert engine.evaluate(20, evidence_gap="x").decision == REJECT
    assert engine.evaluate(90).decision == HIRE


def test_service_and_explanation_agree_on_the_capped_verdict(matcher):
    """A stuffed CV with a high raw score: same capped verdict in decision and explanation."""
    from unittest.mock import MagicMock
    from src.decisioning.calibration import MethodCalibration, ScoreCalibration
    from src.explainability.explainer import MatchingExplainer, RecommendationEngine
    from src.matching.service import run_evaluation

    stuffed = UNRELATED + "\n\nSKILLS\nsql, docker, python, kubernetes, apache spark, apache airflow"
    details = matcher.predict_detailed(stuffed, JOB)
    hybrid = MagicMock()
    hybrid.predict.return_value = {"final_score": 0.9, "component_scores": {}, "weights_used": {},
                                   "skill_details": details}
    models = {"hybrid": hybrid, "skill": matcher, "explainer": MatchingExplainer(extractor=matcher.extractor),
              "recommender": RecommendationEngine(),
              "calibration": ScoreCalibration("t", {"hybrid": MethodCalibration("hybrid", 0.25, 0.40, 0.60)})}
    payload = run_evaluation(models, stuffed, JOB, "hybrid")
    assert payload["result"]["percentage"] == 100.0
    assert payload["decision"].decision == CONSIDER
    rec = payload["explanation"]["hiring_recommendation"]
    assert rec["decision"] == CONSIDER and rec["evidence_gap"]


def test_free_form_uppercase_headings_are_recognised():
    cv = ("PROFESSIONAL SUMMARY\nCareer switcher after a coding bootcamp.\n\n"
          "PROFESSIONAL EXPERIENCE\nSales assistant, 2018-2023.\n\n"
          "TECHNICAL EXPERTISE & SKILLS\nReact, Node.js, SQL, Docker")
    declared, evidence, structured = split_declared_evidence(cv)
    assert structured and "react" in declared.lower() and "react" not in evidence.lower()


def test_job_titles_are_not_taken_for_headings():
    cv = "EXPERIENCE\nTechnology Consultant\nBuilt React and Node.js applications for clients."
    declared, evidence, _ = split_declared_evidence(cv)
    assert declared == "" and "react" in evidence.lower()
