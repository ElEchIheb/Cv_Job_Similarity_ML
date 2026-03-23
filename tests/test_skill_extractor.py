from __future__ import annotations

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

