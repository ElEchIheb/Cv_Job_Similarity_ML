"""
tests/test_pdf_generator.py
Unit tests for the PDF report generator.
"""
from __future__ import annotations

import pytest

# ── Fixtures ──────────────────────────────────────────────────────────────────
SAMPLE_RESULT = {
    "final_score":  0.78,
    "percentage":   78.0,
    "label":        1,
    "confidence":   "high",
    "component_scores": {
        "tfidf_score":     0.72,
        "embedding_score": 0.81,
        "skill_score":     0.76,
    },
    "skill_details": {
        "cv_payload": {
            "hard_skills":    ["Python", "PyTorch", "Docker"],
            "soft_skills":    ["communication", "teamwork"],
            "certifications": [],
            "years_experience": 5,
            "education_level":  "master",
            "domain": "data_science_ml",
        },
        "job_payload": {
            "hard_skills":    ["Python", "PyTorch", "Kubernetes", "Docker"],
            "soft_skills":    ["communication"],
            "certifications": [],
            "years_experience": 0,
            "education_level":  "unknown",
            "domain": "data_science_ml",
        },
        "matching_skills":  ["Python", "PyTorch", "Docker"],
        "missing_skills":   ["Kubernetes"],
        "extra_skills":     [],
        "critical_missing": [],
        "same_domain":      True,
        "coverage": {
            "skill_coverage_text": "3/4 required technical skills"
        },
    },
}

SAMPLE_EXPLANATION = {
    "global_score": 78.0,
    "verdict":      "Strong Match",
    "color":        "green",
    "hiring_recommendation": {
        "decision":      "HIRE",
        "justification": "Strong technical alignment detected.",
        "confidence":    0.87,
    },
    "experience_fit": {
        "candidate_years":           5,
        "estimated_required_years":  3,
        "fit_status": "Exceeds requirements",
        "education_level": "Master",
    },
    "semantic_analysis": {
        "score":           81.0,
        "interpretation":  "Excellent thematic match",
        "key_themes_cv":   ["Python", "PyTorch", "Docker"],
        "key_themes_job":  ["Python", "PyTorch", "Kubernetes"],
        "theme_overlap":   0.67,
    },
    "skill_analysis": {
        "score":            76.0,
        "matching_skills":  ["Python", "PyTorch", "Docker"],
        "missing_skills":   ["Kubernetes"],
        "extra_skills":     [],
        "critical_missing": [],
        "skill_coverage":   "3/4 required technical skills",
    },
    "gap_analysis": {
        "blocking_gaps": [],
        "minor_gaps":    ["Kubernetes — would strengthen the profile"],
        "strengths":     ["Strong alignment in core skills: Python, PyTorch, Docker"],
    },
    "radar_data": {
        "labels":           ["Technical", "Semantic", "Experience", "Soft Skills", "Domain"],
        "cv_scores":        [76.0, 81.0, 100.0, 40.0, 90.0],
        "job_requirements": [85.0, 80.0, 70.0, 65.0, 80.0],
    },
}

SAMPLE_RECOMMENDATIONS = {
    "priority_actions": [
        {
            "skill":      "Kubernetes",
            "importance": "important",
            "resource":   "https://kubernetes.io/docs/home/",
        }
    ],
    "cv_improvements": [
        "List all tools and frameworks used in production environments"
    ],
    "keywords_to_add":         ["Kubernetes", "MLOps", "deployment"],
    "learning_time_estimate":  "~3 weeks to address the main skill gaps",
    "match_potential":         "Up to 91% match if priority gaps are resolved",
}


# ── Tests ─────────────────────────────────────────────────────────────────────
class TestMatchReportPDF:
    """Tests for MatchReportPDF."""

    @pytest.fixture
    def generator(self):
        try:
            from src.reporting.pdf_generator import MatchReportPDF
            return MatchReportPDF()
        except ImportError:
            pytest.skip("reportlab not installed")

    def test_generate_returns_bytes(self, generator):
        pdf = generator.generate(
            result          = SAMPLE_RESULT,
            explanation     = SAMPLE_EXPLANATION,
            recommendations = SAMPLE_RECOMMENDATIONS,
            candidate_name  = "Alice Martin",
            job_title       = "Senior ML Engineer",
        )
        assert isinstance(pdf, bytes)

    def test_pdf_starts_with_pdf_magic_bytes(self, generator):
        pdf = generator.generate(
            result          = SAMPLE_RESULT,
            explanation     = SAMPLE_EXPLANATION,
            recommendations = SAMPLE_RECOMMENDATIONS,
        )
        assert pdf[:4] == b"%PDF"

    def test_pdf_non_empty(self, generator):
        pdf = generator.generate(
            result          = SAMPLE_RESULT,
            explanation     = SAMPLE_EXPLANATION,
            recommendations = SAMPLE_RECOMMENDATIONS,
        )
        assert len(pdf) > 10_000  # a real PDF is never this tiny

    def test_generate_with_minimal_data(self, generator):
        """PDF generation must not crash with minimal/empty data."""
        pdf = generator.generate(
            result          = {"final_score": 0.5, "percentage": 50.0, "label": 0,
                               "confidence": "medium", "component_scores": {},
                               "skill_details": {}},
            explanation     = {"global_score": 50.0, "verdict": "Potential Match",
                               "color": "orange", "skill_analysis": {},
                               "gap_analysis": {"blocking_gaps": [], "minor_gaps": [],
                                                "strengths": []},
                               "radar_data": {}, "semantic_analysis": {}},
            recommendations = {"priority_actions": [], "cv_improvements": [],
                               "keywords_to_add": [], "learning_time_estimate": "N/A",
                               "match_potential": "N/A"},
        )
        assert isinstance(pdf, bytes)
        assert pdf[:4] == b"%PDF"

    def test_generate_with_reject_score(self, generator):
        """Test that REJECT decision path produces valid PDF."""
        result = {**SAMPLE_RESULT, "percentage": 30.0, "final_score": 0.30, "label": 0}
        explanation = {**SAMPLE_EXPLANATION, "global_score": 30.0,
                       "verdict": "Weak Match", "color": "red",
                       "hiring_recommendation": {
                           "decision": "REJECT",
                           "justification": "Score too low.",
                           "confidence": 0.80,
                       }}
        pdf = generator.generate(
            result=result, explanation=explanation,
            recommendations=SAMPLE_RECOMMENDATIONS,
            candidate_name="Bob Smith",
        )
        assert isinstance(pdf, bytes)
        assert len(pdf) > 5_000


class TestChartHelpers:
    """Tests for chart rendering helpers."""

    def test_render_donut_chart(self):
        try:
            from src.reporting.pdf_generator import _render_donut_chart
        except ImportError:
            pytest.skip("reportlab not installed")
        buf = _render_donut_chart(75.0, "Strong Match")
        assert buf.read(4) == b"\x89PNG"

    def test_render_radar_chart(self):
        try:
            from src.reporting.pdf_generator import _render_radar_chart
        except ImportError:
            pytest.skip("reportlab not installed")
        buf = _render_radar_chart(SAMPLE_EXPLANATION["radar_data"])
        assert buf.read(4) == b"\x89PNG"

    def test_render_radar_with_empty_data(self):
        try:
            from src.reporting.pdf_generator import _render_radar_chart
        except ImportError:
            pytest.skip("reportlab not installed")
        buf = _render_radar_chart({})  # should not crash
        assert len(buf.read()) > 0
