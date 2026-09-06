from __future__ import annotations

import re
from typing import Dict, Iterable, List, Set

import numpy as np

from src.nlp.skill_extractor import SkillExtractor
from src.parsing.parser import clean_text

from .base_model import BaseMatchingModel


class SkillMatcher(BaseMatchingModel):
    def __init__(self, extractor: SkillExtractor | None = None) -> None:
        self.extractor = extractor or SkillExtractor()
        self.hard_skills_weight = 0.70
        self.soft_skills_weight = 0.30
        self.last_analysis_: Dict[str, object] = {}

    @staticmethod
    def _score_overlap(source: Set[str], target: Set[str]) -> float:
        if not target:
            return 0.0
        return len(source & target) / len(target)

    @staticmethod
    def _detect_critical_skills(job_text: str, job_skills: Set[str]) -> Set[str]:
        critical = set()
        normalized = clean_text(job_text)
        fragments = re.split(r"(?<=[.;\n])\s*", normalized)
        triggers = ("required", "must", "mandatory", "obligatoire", "essentiel", "indispensable", "need")
        for fragment in fragments:
            if any(trigger in fragment for trigger in triggers):
                for skill in job_skills:
                    if re.search(rf"(?<!\w){re.escape(skill)}(?!\w)", fragment, flags=re.IGNORECASE):
                        critical.add(skill)
        return critical

    def predict_detailed(self, cv: str, job: str) -> Dict[str, object]:
        cv_payload = self.extractor.extract(cv)
        job_payload = self.extractor.extract(job)

        cv_hard = set(cv_payload["hard_skills"])
        job_hard = set(job_payload["hard_skills"])
        cv_soft = set(cv_payload["soft_skills"])
        job_soft = set(job_payload["soft_skills"])
        cv_certifications = set(cv_payload["certifications"])
        job_certifications = set(job_payload["certifications"])

        matching_hard = sorted(cv_hard & job_hard)
        matching_soft = sorted(cv_soft & job_soft)
        missing_hard = sorted(job_hard - cv_hard)
        missing_soft = sorted(job_soft - cv_soft)
        extra_skills = sorted(cv_hard - job_hard)
        critical_skills = self._detect_critical_skills(job, job_hard)
        critical_missing = sorted(critical_skills - cv_hard)
        relevant_certifications = sorted(cv_certifications & job_certifications)

        hard_score = self._score_overlap(cv_hard, job_hard)
        soft_score = self._score_overlap(cv_soft, job_soft)
        
        # Dynamically redistribute weight if a skill category is completely absent in the job posting
        weight_hard = self.hard_skills_weight if job_hard else 0.0
        weight_soft = self.soft_skills_weight if job_soft else 0.0
        total_weight = weight_hard + weight_soft
        
        if total_weight > 0:
            base_score = (weight_hard * hard_score + weight_soft * soft_score) / total_weight
        else:
            base_score = 0.0
            
        domain_bonus = 0.05 if cv_payload.get("domain") == job_payload.get("domain") else 0.0
        certification_bonus = min(0.10, 0.03 * len(relevant_certifications))
        critical_penalty = 0.20 * (len(critical_missing) / len(critical_skills)) if critical_skills else 0.0
        
        final_score = float(np.clip(base_score + domain_bonus + certification_bonus - critical_penalty, 0.0, 1.0))

        self.last_analysis_ = {
            "score": final_score,
            "hard_score": round(hard_score, 4),
            "soft_score": round(soft_score, 4),
            "matching_skills": matching_hard + [skill for skill in matching_soft if skill not in matching_hard],
            "matching_hard_skills": matching_hard,
            "matching_soft_skills": matching_soft,
            "missing_skills": missing_hard + [skill for skill in missing_soft if skill not in missing_hard],
            "missing_hard_skills": missing_hard,
            "missing_soft_skills": missing_soft,
            "extra_skills": extra_skills,
            "critical_missing": critical_missing,
            "relevant_certifications": relevant_certifications,
            "same_domain": cv_payload.get("domain") == job_payload.get("domain"),
            "cv_domain": cv_payload.get("domain"),
            "job_domain": job_payload.get("domain"),
            "cv_payload": cv_payload,
            "job_payload": job_payload,
            "coverage": {
                "hard_coverage": round(hard_score, 4),
                "soft_coverage": round(soft_score, 4),
                "skill_coverage_text": f"{len(matching_hard)}/{len(job_hard) or 1} required skills",
            },
        }
        return self.last_analysis_

    def predict(self, cv: str, job: str) -> float:
        return float(self.predict_detailed(cv, job)["score"])

    def batch_predict(self, cvs: Iterable[str], jobs: Iterable[str]) -> List[float]:
        return [self.predict(cv, job) for cv, job in zip(cvs, jobs)]

    def get_missing_skills(self) -> List[str]:
        return list(self.last_analysis_.get("missing_skills", []))

    def get_matching_skills(self) -> List[str]:
        return list(self.last_analysis_.get("matching_skills", []))

    def get_skill_gap_analysis(self) -> Dict[str, object]:
        return {
            "missing_skills": self.last_analysis_.get("missing_skills", []),
            "critical_missing": self.last_analysis_.get("critical_missing", []),
            "matching_skills": self.last_analysis_.get("matching_skills", []),
            "extra_skills": self.last_analysis_.get("extra_skills", []),
            "coverage": self.last_analysis_.get("coverage", {}),
        }
