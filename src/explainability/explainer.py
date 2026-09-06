"""
src/explainability/explainer.py
Explainability and recommendation engine for JobTest AI Platform.

MatchingExplainer  — produces human-readable analysis from matching results
RecommendationEngine — generates actionable improvement suggestions

All text output is in English for international professional use.
"""
from __future__ import annotations

import logging
from typing import Dict, List

from src.nlp.skill_extractor import SkillExtractor
from src.decisioning import DecisionConfig, DecisionEngine

logger = logging.getLogger(__name__)

_VERDICT_TEXT = {"HIRE": "Strong Match", "CONSIDER": "Potential Match", "REJECT": "Weak Match"}
_VERDICT_COLOR = {"HIRE": "green", "CONSIDER": "orange", "REJECT": "red"}


class MatchingExplainer:
    """Converts raw matching scores into an HR-readable explanation."""

    def __init__(self, extractor: SkillExtractor | None = None) -> None:
        self.extractor = extractor or SkillExtractor()

    # ── Verdict helpers ───────────────────────────────────────────────────────
    @staticmethod
    def _verdict(score: float, optimal_threshold: float = 60.0) -> Dict[str, str]:
        if score >= optimal_threshold + 15.0:
            return {"verdict": "Strong Match", "color": "green"}
        if score >= optimal_threshold:
            return {"verdict": "Potential Match", "color": "orange"}
        return {"verdict": "Weak Match", "color": "red"}

    @staticmethod
    def _hiring_recommendation(score: float, critical_missing: List[str], optimal_threshold: float, confidence_str: str) -> Dict[str, object]:
        """
        Generate a structured hiring recommendation with justification.

        Returns
        -------
        dict with keys: decision, justification, confidence
        """
        has_blockers = len(critical_missing) > 0

        # Translate string confidence back to float for output (High=0.90, Medium=0.65, Low=0.40)
        confidence_val = {"high": 0.90, "medium": 0.65, "low": 0.40}.get(confidence_str, 0.50)

        if score >= optimal_threshold + 15.0 and not has_blockers:
            decision = "HIRE"
            justification = (
                f"Candidate demonstrates strong alignment ({score:.0f}%) with the role requirements. "
                "Technical skills are well-matched, and no critical gaps were identified. "
                "Recommended for immediate interview."
            )
        elif score >= optimal_threshold and not has_blockers:
            decision = "HIRE"
            justification = (
                f"Candidate shows good alignment ({score:.0f}%) with solid technical foundations. "
                "No blocking gaps detected. A standard technical interview is recommended "
                "to validate depth of experience."
            )
        elif score >= optimal_threshold and has_blockers:
            blockers_str = ", ".join(critical_missing[:3])
            decision = "CONSIDER"
            justification = (
                f"Candidate scores {score:.0f}% overall but is missing critical skills: "
                f"{blockers_str}. Consider if training budget allows or if these skills "
                "can be acquired quickly. Conduct a deep technical interview first."
            )
        elif score >= optimal_threshold - 15.0:
            decision = "CONSIDER"
            justification = (
                f"Candidate is a partial fit ({score:.0f}%). "
                "Significant skill gaps exist but the profile shows potential. "
                "Recommend only if no stronger candidates are available."
            )
        else:
            decision = "REJECT"
            justification = (
                f"Candidate score of {score:.0f}% is below the acceptable threshold. "
                "Too many critical skills are missing for the role. "
                "Not recommended without significant re-skilling."
            )

        return {
            "decision": decision,
            "justification": justification,
            "confidence": confidence_val,
        }

    @staticmethod
    def _top_themes(payload: Dict, limit: int = 5) -> List[str]:
        hard_skills = payload.get("hard_skills", [])
        soft_skills = payload.get("soft_skills", [])
        return list(hard_skills + soft_skills)[:limit]

    # ── Main explain ──────────────────────────────────────────────────────────
    def explain(self, cv: str, job: str, hybrid_result: Dict,
                config: "DecisionConfig | None" = None) -> Dict:
        """
        Produce a complete, human-readable explanation of the matching result.

        Parameters
        ----------
        cv : str
            Raw CV text
        job : str
            Raw job description text
        hybrid_result : dict
            Output from HybridMatcher.predict()

        Returns
        -------
        dict with sections: global_score, verdict, semantic_analysis,
            skill_analysis, gap_analysis, radar_data, hiring_recommendation,
            experience_fit
        """
        cv_payload  = hybrid_result.get("skill_details", {}).get("cv_payload")  or self.extractor.extract(cv)
        job_payload = hybrid_result.get("skill_details", {}).get("job_payload") or self.extractor.extract(job)
        scores      = hybrid_result.get("component_scores", {})
        skill_details  = hybrid_result.get("skill_details", {})
        global_score   = float(hybrid_result.get("percentage", 0.0))

        cv_themes   = self._top_themes(cv_payload)
        job_themes  = self._top_themes(job_payload)
        theme_overlap = len(set(cv_themes) & set(job_themes)) / max(1, len(set(job_themes)))

        matching_skills  = skill_details.get("matching_skills", [])
        missing_skills   = skill_details.get("missing_skills", [])
        extra_skills     = skill_details.get("extra_skills", [])
        critical_missing = skill_details.get("critical_missing", [])

        # Radar dimensions (normalised to 0-100)
        years_exp       = float(cv_payload.get("years_experience", 0))
        # Honest "could not detect" state: a parsing failure must NOT masquerade
        # as a confirmed zero (see Bug 1 / BUGFIXES.md). Older payloads without
        # the flag fall back to inferring detection from a positive year count.
        experience_detected     = bool(cv_payload.get("experience_detected", years_exp > 0))
        job_experience_detected = bool(job_payload.get("experience_detected", float(job_payload.get("years_experience", 0)) > 0))
        req_years       = float(job_payload.get("years_experience", 0)) or 3.0
        experience_score = min(100.0, (years_exp / req_years) * 100.0)
        soft_score      = min(100.0, 20.0 * len(cv_payload.get("soft_skills", [])))
        domain_score    = 90.0 if skill_details.get("same_domain") else 50.0
        technique_score = float(scores.get("skill_score", 0.0)) * 100.0
        semantic_score  = float(scores.get("embedding_score", 0.0)) * 100.0

        # ── Required radar vector (Bug 3) ───────────────────────────────────
        # Each "Required" axis is derived from THIS job offer wherever the data
        # model supports it; axes that cannot be derived from JD text today are
        # explicit, labelled hiring benchmarks. `job_requirements_source` tags
        # every axis as "job" (derived) or "benchmark" so the UI/PDF can be
        # honest about which is which. See BUGFIXES.md.
        req_soft_count = len(job_payload.get("soft_skills", []))
        req_soft   = min(100.0, 20.0 * req_soft_count) if req_soft_count else 65.0
        req_domain = 90.0 if job_payload.get("domain", "generalist") != "generalist" else 50.0
        # If the JD states required years, meeting them is the 100% bar; else benchmark.
        req_experience = 100.0 if job_experience_detected else 70.0
        req_technical  = 85.0   # BENCHMARK: target skill coverage (not derivable from JD text)
        req_semantic   = 80.0   # BENCHMARK: target thematic alignment (not derivable from JD text)
        job_requirements        = [req_technical, req_semantic, req_experience, req_soft, req_domain]
        job_requirements_source = [
            "benchmark",
            "benchmark",
            "job" if job_experience_detected else "benchmark",
            "job" if req_soft_count else "benchmark",
            "job",
        ]

        # Strengths (English)
        strengths: List[str] = []
        if matching_skills:
            top_matched = ", ".join(matching_skills[:4])
            strengths.append(f"Strong alignment in core skills: {top_matched}")
        if float(scores.get("embedding_score", 0.0)) >= 0.75:
            strengths.append("Excellent thematic alignment with job description")
        if years_exp >= 5:
            strengths.append(f"Solid professional experience ({years_exp:.0f} years)")
        if years_exp >= 3:
            strengths.append("Mid-level or senior experience profile")
        if skill_details.get("same_domain"):
            strengths.append("Candidate domain matches the job domain")
        if cv_payload.get("certifications"):
            certs = ", ".join(list(cv_payload["certifications"])[:2])
            strengths.append(f"Relevant certifications: {certs}")

        # Gap analysis (English)
        blocking_gaps = [
            f"{skill} — required or strongly expected"
            for skill in critical_missing
        ]
        minor_gaps = [
            f"{skill} — would strengthen the profile"
            for skill in missing_skills
            if skill not in critical_missing
        ][:5]

        # ── Canonical decision via the central DecisionEngine ──────────────
        cfg = config or DecisionConfig.default()
        decision_result = DecisionEngine(cfg).evaluate(
            global_score, cfg, critical_missing=critical_missing
        )
        verdict = {
            "verdict": _VERDICT_TEXT[decision_result.decision],
            "color": _VERDICT_COLOR[decision_result.decision],
        }
        hiring_rec = {
            "decision": decision_result.decision,
            "band_label": decision_result.band_label,
            "justification": decision_result.reason,
            "confidence": decision_result.confidence,          # uncalibrated [0,1]
            "confidence_level": decision_result.confidence_level,
        }

        # Experience fit assessment. "Not detected" is a first-class status,
        # distinct from a candidate with confirmed zero experience.
        if not experience_detected:
            exp_status = "Not detected"
        else:
            exp_status = (
                "Exceeds requirements" if years_exp > req_years * 1.2
                else "Meets requirements" if years_exp >= req_years * 0.8
                else "Below requirements"
            )
        experience_fit = {
            "candidate_years": years_exp,
            "candidate_years_detected": experience_detected,
            "estimated_required_years": req_years,
            "required_years_detected": job_experience_detected,
            "fit_status": exp_status,
            "education_level": cv_payload.get("education_level", "unknown").capitalize(),
        }

        return {
            "global_score": round(global_score, 1),
            "decision_config": cfg.as_dict(),
            **verdict,
            "hiring_recommendation": hiring_rec,
            "experience_fit": experience_fit,
            "semantic_analysis": {
                "score": round(semantic_score, 1),
                "interpretation": (
                    "Excellent thematic match"
                    if semantic_score >= 75
                    else "Moderate semantic alignment"
                    if semantic_score >= 55
                    else "Low semantic alignment"
                ),
                "key_themes_cv":  cv_themes,
                "key_themes_job": job_themes,
                "theme_overlap":  round(theme_overlap, 2),
            },
            "skill_analysis": {
                "score":            round(technique_score, 1),
                "matching_skills":  matching_skills,
                "missing_skills":   missing_skills,
                "extra_skills":     extra_skills,
                "critical_missing": critical_missing,
                "skill_coverage":   skill_details.get("coverage", {}).get(
                    "skill_coverage_text", "0/0 required skills"
                ),
            },
            "gap_analysis": {
                "blocking_gaps": blocking_gaps,
                "minor_gaps":    minor_gaps,
                "strengths":     strengths or ["Profile is coherent but limited discriminating signals detected"],
            },
            "radar_data": {
                "labels":           ["Technical", "Semantic", "Experience", "Soft Skills", "Domain"],
                "cv_scores":        [
                    round(technique_score, 1),
                    round(semantic_score, 1),
                    round(experience_score, 1),
                    round(soft_score, 1),
                    round(domain_score, 1),
                ],
                # Per-job required vector (Bug 3): derived where the data allows,
                # labelled benchmark otherwise via job_requirements_source.
                "job_requirements":        [round(v, 1) for v in job_requirements],
                "job_requirements_source": job_requirements_source,
                # The Experience axis reads 0 when experience could not be parsed;
                # this flag lets the UI render that as "N/A" rather than a real 0.
                "experience_detected":     experience_detected,
            },
        }


class RecommendationEngine:
    """Generates actionable recommendations based on gap analysis."""

    # Expanded resource map — more technologies covered
    RESOURCE_MAP: Dict[str, str] = {
        # ML / AI
        "python":        "https://docs.python.org/3/tutorial/",
        "machine learning": "https://scikit-learn.org/stable/user_guide.html",
        "deep learning": "https://pytorch.org/tutorials/",
        "pytorch":       "https://pytorch.org/tutorials/",
        "tensorflow":    "https://www.tensorflow.org/tutorials",
        "mlflow":        "https://mlflow.org/docs/latest/index.html",
        "nlp":           "https://huggingface.co/learn/nlp-course/",
        "llm":           "https://huggingface.co/learn/nlp-course/",
        "transformers":  "https://huggingface.co/docs/transformers/",
        # DevOps / Cloud
        "kubernetes":    "https://kubernetes.io/docs/home/",
        "docker":        "https://docs.docker.com/get-started/",
        "aws":           "https://docs.aws.amazon.com/",
        "azure":         "https://learn.microsoft.com/azure/",
        "gcp":           "https://cloud.google.com/docs",
        "terraform":     "https://developer.hashicorp.com/terraform/docs",
        "ci/cd":         "https://docs.gitlab.com/ee/ci/",
        "github actions":"https://docs.github.com/actions",
        # Data
        "spark":         "https://spark.apache.org/docs/latest/",
        "airflow":       "https://airflow.apache.org/docs/",
        "dbt":           "https://docs.getdbt.com/",
        "sql":           "https://www.postgresql.org/docs/",
        "postgresql":    "https://www.postgresql.org/docs/",
        # Web
        "react":         "https://react.dev/",
        "fastapi":       "https://fastapi.tiangolo.com/",
        "node.js":       "https://nodejs.org/en/docs/",
        "typescript":    "https://www.typescriptlang.org/docs/",
        # Architecture
        "microservices": "https://microservices.io/",
        "system design": "https://github.com/donnemartin/system-design-primer",
    }

    _DEFAULT_RESOURCE = "https://roadmap.sh/"

    def generate(self, gap_analysis: Dict) -> Dict:
        """
        Generate prioritised recommendations from gap analysis.

        Parameters
        ----------
        gap_analysis : dict
            Output from MatchingExplainer.explain()['gap_analysis']

        Returns
        -------
        dict with keys: priority_actions, cv_improvements, keywords_to_add,
            learning_time_estimate, match_potential
        """
        blocking_gaps = gap_analysis.get("blocking_gaps", [])
        minor_gaps    = gap_analysis.get("minor_gaps", [])
        strengths     = gap_analysis.get("strengths", [])

        def _gap_to_action(gap: str, importance: str) -> Dict[str, str]:
            skill    = gap.split(" — ")[0].strip()
            resource = self.RESOURCE_MAP.get(skill.lower(), self._DEFAULT_RESOURCE)
            return {"skill": skill, "importance": importance, "resource": resource}

        priority_actions = [_gap_to_action(gap, "critical") for gap in blocking_gaps]
        priority_actions.extend(
            _gap_to_action(gap, "important") for gap in minor_gaps[:3]
        )

        critical_count = len(blocking_gaps)
        cv_improvements = [
            "List all tools and frameworks used in production environments",
            "Quantify achievements with concrete metrics (e.g., '30% performance improvement')",
            "Highlight project deliverables, business impact, and leadership responsibilities",
            "Tailor your CV summary to the specific job description",
        ]
        if critical_count:
            cv_improvements.append(
                "Make critical skills explicit — mention specific versions and project contexts"
            )

        keywords_to_add = sorted(
            {action["skill"] for action in priority_actions} | {"MLOps", "deployment", "collaboration"}
        )
        learning_weeks   = max(2, critical_count * 2 + max(1, len(minor_gaps)))
        match_potential  = min(98, 70 + critical_count * 6 + len(minor_gaps) * 2 + len(strengths) * 3)

        return {
            "priority_actions":         priority_actions,
            "cv_improvements":          cv_improvements,
            "keywords_to_add":          keywords_to_add[:8],
            "learning_time_estimate":   f"~{learning_weeks} weeks to address the main skill gaps",
            "match_potential":          f"Up to {match_potential}% match if priority gaps are resolved",
        }
