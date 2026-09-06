from __future__ import annotations

from datetime import date

from src.models.skill_matcher import SkillMatcher
from src.nlp.skill_extractor import SkillExtractor


def test_skill_extractor_detects_variants_and_metadata():
    extractor = SkillExtractor()
    text = (
        "ML engineer with 5 years of experience in JS, Python, Kubernetes and AWS. "
        "Master degree. Strong communication and teamwork."
    )
    payload = extractor.extract(text)
    assert "machine learning" in payload["hard_skills"]
    assert "javascript" in payload["hard_skills"]
    assert "python" in payload["hard_skills"]
    assert payload["years_experience"] == 5
    assert payload["education_level"] == "master"
    assert "communication" in payload["soft_skills"]
    assert payload["confidence_scores"]["python"] >= 0.45


def test_skill_extractor_detects_domain():
    extractor = SkillExtractor()
    payload = extractor.extract("Built NLP pipelines with transformers, hugging face, rag and vector database.")
    assert payload["domain"] == "ai_nlp"


# ── Bug 1: experience extraction from date ranges ─────────────────────────────

def test_experience_endash_range():
    payload = SkillExtractor().extract("Full Stack Web Developer — TechSolutions, 2023–2026")
    assert payload["years_experience"] == 3
    assert payload["experience_detected"] is True


def test_experience_hyphen_range_survives_phone_scrubbing():
    # Regression: clean_text() used to strip "2023-2026" as a phone number, so a
    # compact hyphen range must still be detected from the raw text.
    payload = SkillExtractor().extract("Backend Developer, TechSolutions, 2023-2026")
    assert payload["years_experience"] == 3
    assert payload["experience_detected"] is True


def test_experience_present_ended_range():
    start = date.today().year - 4
    payload = SkillExtractor().extract(f"Senior Engineer, {start} - present")
    assert payload["experience_detected"] is True
    assert payload["years_experience"] == 4


def test_experience_multiple_entries_are_summed():
    payload = SkillExtractor().extract(
        "Developer A — 2015-2018\nDeveloper B — 2019-2022"
    )
    assert payload["years_experience"] == 6  # 3 + 3, summed across entries
    assert payload["experience_detected"] is True


def test_experience_explicit_years_still_supported():
    payload = SkillExtractor().extract("Engineer with 7 years of hands-on experience")
    assert payload["years_experience"] == 7
    assert payload["experience_detected"] is True


def test_experience_not_detected_is_honest_not_zero():
    # A genuinely empty experience section must be an honest "not detected"
    # (detected=False), NOT silently scored the same as confirmed zero years.
    payload = SkillExtractor().extract("Motivated recent graduate seeking opportunities.")
    assert payload["years_experience"] == 0
    assert payload["experience_detected"] is False


# ── Bug 2: common/short web skills and full coverage denominator ──────────────

def test_common_web_skills_are_recognized():
    payload = SkillExtractor().extract("Skills: HTML, CSS, HTML5, CSS3, SCSS, JavaScript")
    hard = payload["hard_skills"]
    assert "html" in hard  # incl. HTML5 alias
    assert "css" in hard   # incl. CSS3 alias
    assert "sass" in hard  # SCSS alias


def test_full_coverage_when_cv_lists_all_required_skills():
    # When the CV contains every skill in the job's required list verbatim, the
    # engine must report N/N for the ACTUAL N — no skill may silently vanish
    # from both the matched and missing buckets.
    required = ["HTML", "CSS", "JavaScript", "React", "Node.js",
                "Express", "MongoDB", "SQL", "Git", "REST API", "Docker"]
    job = "Full Stack Web Developer. Required skills: " + ", ".join(required) + "."
    cv = "Full Stack Web Developer. Proficient in " + ", ".join(required) + "."

    matcher = SkillMatcher()
    analysis = matcher.predict_detailed(cv, job)

    n = len(analysis["job_payload"]["hard_skills"])
    assert n == 11, f"expected all 11 required skills recognized, got {n}"
    assert analysis["coverage"]["skill_coverage_text"] == "11/11 required skills"
    assert analysis["missing_hard_skills"] == []
    # Every required skill lands in exactly one bucket (matched XOR missing).
    matched = set(analysis["matching_hard_skills"])
    missing = set(analysis["missing_hard_skills"])
    job_hard = set(analysis["job_payload"]["hard_skills"])
    assert matched | missing == job_hard
    assert matched & missing == set()

