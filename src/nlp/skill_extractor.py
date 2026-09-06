from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

from src.parsing.parser import clean_text, tokenize_and_normalize

try:
    import spacy  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    spacy = None


class SkillExtractor:
    """Hybrid skill extractor combining dictionary lookup, rule-based NER and n-grams."""

    DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "datasets" / "skills_dictionary.json"

    def __init__(self, dictionary_path: Optional[str] = None) -> None:
        self.dictionary_path = Path(dictionary_path) if dictionary_path else self.DEFAULT_PATH
        self.dictionary = self._load_dictionary(self.dictionary_path)
        self.hard_skill_categories = self.dictionary.get("hard_skills", {})
        self.soft_skills = {self._normalize_phrase(skill): skill for skill in self.dictionary.get("soft_skills", [])}
        self.certifications = {self._normalize_phrase(skill): skill for skill in self.dictionary.get("certifications", [])}
        self.variants = {
            "ml": "machine learning",
            "dl": "deep learning",
            "nlp": "nlp",
            "llm": "llm",
            "rag": "rag",
            "js": "javascript",
            "ts": "typescript",
            "py": "python",
            "k8s": "kubernetes",
            "postgres": "postgresql",
            "node": "node.js",
            "ci cd": "ci/cd",
            "githubactions": "github actions",
        }
        self.variants.update({self._normalize_phrase(alias): target for alias, target in self.dictionary.get("aliases", {}).items()})
        self.domain_keywords = self.dictionary.get("domain_keywords", {})
        self.hard_lookup, self.skill_to_category = self._build_hard_skill_lookup()
        self.pattern_cache = self._build_pattern_cache()
        self.ner = self._build_ner_pipeline()

    @staticmethod
    def _load_dictionary(path: Path) -> Dict[str, object]:
        if not path.exists():
            raise FileNotFoundError(f"Skills dictionary not found: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _normalize_phrase(phrase: str) -> str:
        normalized = clean_text(phrase)
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.strip()

    def _build_hard_skill_lookup(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        lookup: Dict[str, str] = {}
        categories: Dict[str, str] = {}
        for category, skills in self.hard_skill_categories.items():
            for skill in skills:
                normalized = self._normalize_phrase(skill)
                lookup[normalized] = skill
                categories[skill] = category
                categories[normalized] = category
                collapsed = normalized.replace(" ", "")
                if collapsed != normalized:
                    lookup[collapsed] = skill
        return lookup, categories

    def _build_pattern_cache(self) -> Dict[str, re.Pattern[str]]:
        cache = {}
        all_terms = set(self.hard_lookup) | set(self.soft_skills) | set(self.certifications)
        for term in all_terms:
            escaped = re.escape(term).replace(r"\ ", r"\s+")
            cache[term] = re.compile(rf"(?<!\w){escaped}(?!\w)", re.IGNORECASE)
        return cache

    def _build_ner_pipeline(self):  # pragma: no cover - only exercised if spaCy is installed
        if spacy is None:
            return None
        nlp = spacy.blank("en")
        ruler = nlp.add_pipe("entity_ruler")
        patterns = []
        for normalized, original in self.hard_lookup.items():
            label = self._infer_label(original)
            patterns.append({"label": label, "pattern": original})
        for original in self.certifications.values():
            patterns.append({"label": "CERTIFICATION", "pattern": original})
        ruler.add_patterns(patterns)
        return nlp

    def _infer_label(self, skill: str) -> str:
        category = self.skill_to_category.get(skill, self.skill_to_category.get(self._normalize_phrase(skill), ""))
        if category == "programming":
            return "LANGUAGE"
        if category in {"web", "mobile", "ai_ml", "testing", "architecture"}:
            return "FRAMEWORK"
        if category in {"tools", "cloud", "devops", "databases"}:
            return "TOOL"
        return "SKILL"

    def _apply_variants(self, text: str) -> str:
        expanded = f" {clean_text(text)} "
        for alias, canonical in self.variants.items():
            expanded = re.sub(rf"(?<!\w){re.escape(alias)}(?!\w)", canonical, expanded, flags=re.IGNORECASE)
        return expanded

    def _dictionary_matches(self, text: str) -> Counter:
        matches: Counter = Counter()
        expanded = self._apply_variants(text)
        for normalized, original in self.hard_lookup.items():
            if self.pattern_cache[normalized].search(expanded):
                matches[original] += 1
        for normalized, original in self.soft_skills.items():
            if self.pattern_cache[normalized].search(expanded):
                matches[original] += 1
        for normalized, original in self.certifications.items():
            if self.pattern_cache[normalized].search(expanded):
                matches[original] += 1
        return matches

    def _ner_matches(self, text: str) -> Dict[str, List[str]]:
        if self.ner is None:
            return {"skills": [], "certifications": []}
        doc = self.ner(text)
        skills = []
        certifications = []
        for entity in doc.ents:
            if entity.label_ == "CERTIFICATION":
                certifications.append(entity.text)
            else:
                skills.append(entity.text)
        return {"skills": skills, "certifications": certifications}

    def _ngram_matches(self, text: str) -> Counter:
        tokens = tokenize_and_normalize(text)
        ngram_matches: Counter = Counter()
        whitelist = set(self.hard_lookup) | set(self.soft_skills) | set(self.certifications)
        for n in (1, 2, 3):
            for index in range(len(tokens) - n + 1):
                candidate = " ".join(tokens[index : index + n])
                canonical_candidate = self.variants.get(candidate, candidate)
                for probe in (candidate, canonical_candidate, candidate.replace(" ", "")):
                    if probe in whitelist:
                        original = self.hard_lookup.get(probe) or self.soft_skills.get(probe) or self.certifications.get(probe)
                        if original:
                            ngram_matches[original] += 1
                            break
        return ngram_matches

    # Month names (English + French, full and common abbreviations) → month number.
    _MONTHS = {
        "jan": 1, "january": 1, "janvier": 1,
        "feb": 2, "february": 2, "fevrier": 2, "février": 2, "fev": 2, "fév": 2,
        "mar": 3, "march": 3, "mars": 3,
        "apr": 4, "april": 4, "avril": 4, "avr": 4,
        "may": 5, "mai": 5,
        "jun": 6, "june": 6, "juin": 6,
        "jul": 7, "july": 7, "juillet": 7, "juil": 7,
        "aug": 8, "august": 8, "aout": 8, "août": 8,
        "sep": 9, "sept": 9, "september": 9, "septembre": 9,
        "oct": 10, "october": 10, "octobre": 10,
        "nov": 11, "november": 11, "novembre": 11,
        "dec": 12, "december": 12, "decembre": 12, "décembre": 12, "déc": 12,
    }
    # Tokens that mark an open-ended (still-ongoing) role → resolves to today.
    _PRESENT_TOKENS = {
        "present", "présent", "current", "now", "today", "actuel", "actuelle",
        "ongoing", "aujourd'hui", "aujourd’hui", "todate", "to date", "en cours",
    }
    # A single date range: optional month name + year, a separator, then an
    # optional month name + (year | present-token). Years are boundary-guarded so
    # we never grab digits from inside a longer number.
    _RANGE_RE = re.compile(
        r"(?:(?P<sm>[a-zéûôàèçé]{3,9})[.\s]+)?"
        r"(?<!\d)(?P<sy>(?:19|20)\d{2})(?!\d)"
        r"\s*(?:[-–—]|to|until|au|à|jusqu['’]?\s*(?:au|à)?)\s*"
        r"(?:(?P<em>[a-zéûôàèçé]{3,9})[.\s]+)?"
        r"(?P<ey>(?:19|20)\d{2}|present|présent|current|now|today|actuel(?:le)?|ongoing|aujourd['’]hui|en\s+cours)",
        re.IGNORECASE,
    )

    @classmethod
    def _detect_years_experience(cls, text: str) -> Optional[float]:
        """Estimate total years of professional experience from *raw* CV text.

        Returns ``None`` (an honest "could not detect" state) when neither an
        explicit "N years" phrase nor a parseable date range is present, so
        callers can distinguish a parsing failure from a confirmed zero. The
        caller MUST pass raw text: :func:`clean_text` scrubs compact
        ``YYYY-YYYY`` ranges as if they were phone numbers, which is exactly how
        well-formatted date ranges used to go undetected.
        """
        normalized = (text or "").lower()
        today = date.today()

        # 1) Explicit "N years"/"N ans" (kept from the original behaviour).
        explicit = [
            int(value)
            for value in re.findall(
                r"(\d{1,2})\s*\+?\s*(?:years?|yrs?|ans?|annees?|années?)",
                normalized,
                flags=re.IGNORECASE,
            )
        ]
        explicit_max = float(max(explicit)) if explicit else 0.0

        # 2) Date ranges — summed across every entry (multiple jobs add up).
        range_total = 0.0
        found_range = False
        for match in cls._RANGE_RE.finditer(normalized):
            start_year = int(match.group("sy"))
            end_raw = match.group("ey").strip().lower()
            start_month = cls._MONTHS.get((match.group("sm") or "").strip().lower())
            end_month = cls._MONTHS.get((match.group("em") or "").strip().lower())

            if end_raw in cls._PRESENT_TOKENS or not end_raw[:4].isdigit():
                end_year, resolved_end_month = today.year, today.month
            else:
                end_year, resolved_end_month = int(end_raw[:4]), None

            has_months = start_month is not None or end_month is not None
            if has_months:
                s_m = start_month or 1
                e_m = resolved_end_month or end_month or 12
                duration = ((end_year * 12 + (e_m - 1)) - (start_year * 12 + (s_m - 1))) / 12.0
            else:
                duration = float(end_year - start_year)

            if 0.0 <= duration <= 60.0:  # ignore reversed or absurd ranges
                range_total += duration
                found_range = True

        if not explicit and not found_range:
            return None
        return round(max(explicit_max, range_total), 1)

    @staticmethod
    def _detect_education_level(text: str) -> str:
        normalized = clean_text(text)
        if re.search(r"\b(phd|doctorat|doctorate)\b", normalized):
            return "phd"
        if re.search(r"\b(master|msc|mba|ingenieur|ing[ée]nieur)\b", normalized):
            return "master"
        if re.search(r"\b(bachelor|licence|bsc)\b", normalized):
            return "bachelor"
        if re.search(r"\b(dut|bts|associate|technician|technicien)\b", normalized):
            return "associate"
        return "unknown"

    def detect_domain(self, text: str) -> str:
        normalized = self._apply_variants(text)
        domain_keywords = self.domain_keywords or {
            "data_science_ml": {"python", "pandas", "scikit-learn", "tensorflow", "pytorch", "machine learning"},
            "full_stack": {"react", "nodejs", "typescript", "postgresql", "rest api"},
            "devops_cloud": {"aws", "docker", "kubernetes", "terraform", "ci/cd"},
            "cybersecurity": {"owasp", "siem", "soc", "penetration testing", "zero trust"},
            "mobile": {"android", "ios", "swift", "kotlin", "flutter"},
            "backend": {"java", "spring boot", "microservices", "grpc", "redis"},
            "frontend": {"react", "vue", "angular", "figma", "css"},
            "data_engineering": {"spark", "airflow", "dbt", "hadoop", "etl"},
            "ai_nlp": {"nlp", "llm", "rag", "transformers", "spacy"},
            "architecture": {"software architecture", "event-driven architecture", "ddd", "microservices"},
        }
        scores = {}
        for domain, keywords in domain_keywords.items():
            scores[domain] = sum(1 for keyword in keywords if re.search(rf"(?<!\w){re.escape(keyword)}(?!\w)", normalized, flags=re.IGNORECASE))
        best_domain, best_score = max(scores.items(), key=lambda item: item[1])
        return best_domain if best_score > 0 else "generalist"

    def extract(self, text: str) -> Dict[str, object]:
        # Detect experience from the RAW text: clean_text (used by _apply_variants
        # below) strips compact YYYY-YYYY ranges as phone numbers, so date-range
        # parsing must see the original string.
        detected_years = self._detect_years_experience(text)
        normalized = self._apply_variants(text)
        dictionary_hits = self._dictionary_matches(normalized)
        ner_hits = self._ner_matches(normalized)
        ngram_hits = self._ngram_matches(normalized)

        support: Dict[str, Set[str]] = defaultdict(set)
        hard_skills: Set[str] = set()
        soft_skills: Set[str] = set()
        certifications: Set[str] = set()

        for skill in dictionary_hits:
            support[skill].add("dictionary")
        for skill in ngram_hits:
            support[skill].add("ngram")
        for skill in ner_hits["skills"]:
            canonical = self.hard_lookup.get(self._normalize_phrase(skill), skill)
            support[canonical].add("ner")
        for certification in ner_hits["certifications"]:
            canonical = self.certifications.get(self._normalize_phrase(certification), certification)
            support[canonical].add("ner")

        for skill, layers in support.items():
            normalized_skill = self._normalize_phrase(skill)
            canonical = self.hard_lookup.get(normalized_skill) or self.soft_skills.get(normalized_skill) or self.certifications.get(normalized_skill) or skill
            if canonical in self.certifications.values():
                certifications.add(canonical)
            elif canonical in self.soft_skills.values():
                soft_skills.add(canonical)
            else:
                hard_skills.add(canonical)

        confidence_scores = {}
        for skill, layers in support.items():
            canonical = self.hard_lookup.get(self._normalize_phrase(skill)) or self.soft_skills.get(self._normalize_phrase(skill)) or self.certifications.get(self._normalize_phrase(skill)) or skill
            layer_boost = len(layers) / 3.0
            mention_boost = min(0.3, 0.1 * (dictionary_hits.get(canonical, 0) + ngram_hits.get(canonical, 0)))
            confidence_scores[canonical] = round(min(0.99, 0.45 + layer_boost + mention_boost), 3)

        certifications.update(
            certificate
            for normalized_certificate, certificate in self.certifications.items()
            if self.pattern_cache[normalized_certificate].search(normalized)
        )

        return {
            "hard_skills": sorted(hard_skills),
            "soft_skills": sorted(soft_skills),
            "certifications": sorted(certifications),
            "years_experience": detected_years if detected_years is not None else 0,
            "experience_detected": detected_years is not None,
            "education_level": self._detect_education_level(normalized),
            "confidence_scores": dict(sorted(confidence_scores.items())),
            "domain": self.detect_domain(normalized),
        }
