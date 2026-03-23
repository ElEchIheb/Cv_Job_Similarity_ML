from __future__ import annotations

from typing import Dict, List

from src.nlp.skill_extractor import SkillExtractor


class MatchingExplainer:
    def __init__(self, extractor: SkillExtractor | None = None) -> None:
        self.extractor = extractor or SkillExtractor()

    @staticmethod
    def _verdict(score: float) -> Dict[str, str]:
        if score >= 80:
            return {"verdict": "Bon candidat", "color": "green"}
        if score >= 60:
            return {"verdict": "Candidat a considerer", "color": "orange"}
        return {"verdict": "Matching faible", "color": "red"}

    @staticmethod
    def _top_themes(payload: Dict[str, object], limit: int = 5) -> List[str]:
        hard_skills = payload.get("hard_skills", [])
        soft_skills = payload.get("soft_skills", [])
        combined = list(hard_skills) + list(soft_skills)
        return combined[:limit]

    def explain(self, cv: str, job: str, hybrid_result: Dict[str, object]) -> Dict[str, object]:
        cv_payload = hybrid_result.get("skill_details", {}).get("cv_payload") or self.extractor.extract(cv)
        job_payload = hybrid_result.get("skill_details", {}).get("job_payload") or self.extractor.extract(job)
        scores = hybrid_result.get("component_scores", {})
        skill_details = hybrid_result.get("skill_details", {})
        global_score = float(hybrid_result.get("percentage", 0.0))
        verdict = self._verdict(global_score)

        cv_themes = self._top_themes(cv_payload)
        job_themes = self._top_themes(job_payload)
        theme_overlap = len(set(cv_themes) & set(job_themes)) / max(1, len(set(job_themes)))
        matching_skills = skill_details.get("matching_skills", [])
        missing_skills = skill_details.get("missing_skills", [])
        extra_skills = skill_details.get("extra_skills", [])
        critical_missing = skill_details.get("critical_missing", [])

        experience_score = min(100.0, float(cv_payload.get("years_experience", 0)) * 10.0)
        soft_score = min(100.0, 25.0 * len(cv_payload.get("soft_skills", [])))
        domain_score = 85.0 if skill_details.get("same_domain") else 45.0
        technique_score = float(scores.get("skill_score", 0.0)) * 100.0
        semantic_score = float(scores.get("embedding_score", 0.0)) * 100.0

        strengths = []
        if matching_skills:
            strengths.append(f"Competences alignees: {', '.join(matching_skills[:4])}")
        if float(scores.get("embedding_score", 0.0)) >= 0.75:
            strengths.append("Tres bonne correspondance thematique")
        if float(cv_payload.get("years_experience", 0)) >= 5:
            strengths.append("Experience professionnelle solide")

        blocking_gaps = [f"{skill} - requis ou fortement attendu" for skill in critical_missing]
        minor_gaps = [f"{skill} - a renforcer" for skill in missing_skills if skill not in critical_missing][:5]

        return {
            "global_score": round(global_score, 1),
            **verdict,
            "semantic_analysis": {
                "score": round(semantic_score, 1),
                "interpretation": "Tres bonne correspondance thematique" if semantic_score >= 75 else "Correspondance semantique moyenne",
                "key_themes_cv": cv_themes,
                "key_themes_job": job_themes,
                "theme_overlap": round(theme_overlap, 2),
            },
            "skill_analysis": {
                "score": round(float(scores.get("skill_score", 0.0)) * 100.0, 1),
                "matching_skills": matching_skills,
                "missing_skills": missing_skills,
                "extra_skills": extra_skills,
                "critical_missing": critical_missing,
                "skill_coverage": skill_details.get("coverage", {}).get("skill_coverage_text", "0/0 competences requises"),
            },
            "gap_analysis": {
                "blocking_gaps": blocking_gaps,
                "minor_gaps": minor_gaps,
                "strengths": strengths or ["Profil coherent mais peu d'elements discriminants detectes"],
            },
            "radar_data": {
                "labels": ["Technique", "Semantique", "Experience", "Soft Skills", "Domaine"],
                "cv_scores": [
                    round(technique_score, 1),
                    round(semantic_score, 1),
                    round(experience_score, 1),
                    round(soft_score, 1),
                    round(domain_score, 1),
                ],
                "job_requirements": [85.0, 80.0, 70.0, 65.0, 80.0],
            },
        }


class RecommendationEngine:
    RESOURCE_MAP = {
        "mlflow": "https://mlflow.org/docs/latest/index.html",
        "kubernetes": "https://kubernetes.io/docs/home/",
        "docker": "https://docs.docker.com/",
        "aws": "https://docs.aws.amazon.com/",
        "azure": "https://learn.microsoft.com/azure/",
        "gcp": "https://cloud.google.com/docs",
        "spark": "https://spark.apache.org/docs/latest/",
        "airflow": "https://airflow.apache.org/docs/",
        "dbt": "https://docs.getdbt.com/",
        "react": "https://react.dev/",
        "fastapi": "https://fastapi.tiangolo.com/",
        "terraform": "https://developer.hashicorp.com/terraform/docs",
    }

    def generate(self, gap_analysis: Dict[str, object]) -> Dict[str, object]:
        blocking_gaps = gap_analysis.get("blocking_gaps", [])
        minor_gaps = gap_analysis.get("minor_gaps", [])
        strengths = gap_analysis.get("strengths", [])

        def _gap_to_action(gap: str, importance: str) -> Dict[str, str]:
            skill = gap.split(" - ")[0]
            resource = self.RESOURCE_MAP.get(skill.lower(), "https://roadmap.sh/")
            return {"skill": skill, "importance": importance, "resource": resource}

        priority_actions = [_gap_to_action(gap, "critique") for gap in blocking_gaps]
        priority_actions.extend(_gap_to_action(gap, "importante") for gap in minor_gaps[:3])

        critical_count = len(blocking_gaps)
        improvement_hints = [
            "Ajouter les outils et frameworks utilises en production",
            "Quantifier les resultats obtenus avec des chiffres",
            "Mettre en avant les livrables, l'impact metier et les responsabilites",
        ]
        if critical_count:
            improvement_hints.append("Rendre explicites les competences critiques qui apparaissent deja dans vos projets")

        keywords_to_add = sorted({action["skill"] for action in priority_actions} | {"MLOps", "deployment", "collaboration"})
        learning_weeks = max(2, critical_count * 2 + max(1, len(minor_gaps)))
        match_potential = min(98, 70 + critical_count * 6 + len(minor_gaps) * 2 + len(strengths) * 3)

        return {
            "priority_actions": priority_actions,
            "cv_improvements": improvement_hints,
            "keywords_to_add": keywords_to_add[:8],
            "learning_time_estimate": f"~{learning_weeks} semaines pour reduire les principaux ecarts",
            "match_potential": f"Potentiel {match_potential}% si les gaps prioritaires sont combles",
        }
