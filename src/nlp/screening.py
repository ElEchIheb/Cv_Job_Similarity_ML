"""
src/nlp/screening.py
Evidence screening applied to a CV before it is scored against an offer.

Three checks, each explainable and reported with the result:

1. Text copied from the offer. Runs of at least ``COPY_MIN_TOKENS``
   consecutive tokens that also appear in the offer are removed from the CV
   before ANY component is computed. On the 12 000 synthetic pairs the longest
   legitimate common run is 7 tokens, so genuine pairs are untouched; pasting
   the offer's requirement list into a CV no longer raises the score.
2. Negated mentions ("no experience with Kubernetes", "sans Docker", "je ne
   maîtrise pas Spark") are ignored when extracting the CV's skills, and the
   negated clauses that name a skill are also removed from the text given to
   TF-IDF and embeddings.
3. Declared versus demonstrated skills. A skill that only appears in a skills
   list (a "Skills / Compétences / Technologies" section or an inline
   "Skills: ..." line) is *declared*; a skill that appears in the experience,
   projects, summary or certifications text is *demonstrated* (a certification
   is external evidence). When the CV has no recognisable
   section heading the distinction cannot be made and every mention counts as
   demonstrated (reported as ``structure_detected = False``).

The decision layer uses this report to withhold HIRE when the matched skills
rest mostly on declarations or on copied text (see ``evidence_insufficient``).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

COPY_MIN_TOKENS = 8
DECLARED_SKILL_WEIGHT = 0.5          # a declared-only skill counts for half
MIN_DEMONSTRATED_SHARE = 0.5         # HIRE needs >= half of matched skills demonstrated

_TOKEN = re.compile(r"[\w+#.]+", re.UNICODE)

_HEADING_WORDS = {
    "declared": r"skills|technical skills|hard skills|soft skills|key skills|core competencies|competences?|"
                r"comp[ée]tences?(?: techniques| cl[ée]s)?|stack(?: technique)?|tech stack|outils|tools|"
                r"technologies|expertise|languages?|langues?|interests|centres? d'int[ée]r[êe]t",
    "evidence": r"summary|profil|profile|about|objectif|objective|r[ée]sum[ée]|presentation|pr[ée]sentation|"
                r"experiences?|exp[ée]riences?(?: professionnelles?)?|work experience|professional experience|"
                r"employment|career|parcours(?: professionnel)?|projects?|projets?|r[ée]alisations|"
                r"achievements|education|formation|dipl[ôo]mes?|certifications?",
}
_HEADING_LINE = {k: re.compile(rf"^\s*(?:{v})\s*:?\s*$", re.IGNORECASE) for k, v in _HEADING_WORDS.items()}
_INLINE_DECLARED = re.compile(rf"^\s*(?:{_HEADING_WORDS['declared']})\s*:\s*\S", re.IGNORECASE)
# Free-form headings such as "PROFESSIONAL SUMMARY" or "TECHNICAL EXPERTISE &
# SKILLS": a short line (at most 6 words, no final punctuation) containing a
# section keyword. Experience-type keywords win when both kinds appear.
_KEYWORDS = {
    "evidence": re.compile(r"summary|profil|about|objecti|experience|exp[ée]rience|employment|career|parcours|"
                           r"project|projet|r[ée]alisation|achievement|education|formation|dipl[ôo]me|certification",
                           re.IGNORECASE),
    "declared": re.compile(r"skill|comp[ée]tence|competence|technolog|expertise|stack|tools|outils|"
                           r"language|langue|interest|int[ée]r[êe]t", re.IGNORECASE),
}


def _heading_kind(line: str):
    """'evidence' / 'declared' when the line is a section heading, else None."""
    if len(line) > 45 or line.endswith((".", ",", ";")) or len(line.split()) > 6:
        return None
    if _HEADING_LINE["declared"].match(line):
        return "declared"
    if _HEADING_LINE["evidence"].match(line):
        return "evidence"
    letters = [c for c in line if c.isalpha()]
    looks_like_heading = line.rstrip().endswith(":") or (letters and sum(c.isupper() for c in letters) / len(letters) > 0.6)
    if not looks_like_heading:
        return None
    if _KEYWORDS["evidence"].search(line):
        return "evidence"
    if _KEYWORDS["declared"].search(line):
        return "declared"
    return None

# A dot ends a clause only when followed by a space or the end of the text, so
# skill names such as "node.js" or "next.js" are not split.
_CLAUSE_SPLIT = re.compile(r"\n|\.(?=\s|$)|[;!?]|\bbut\b|\bmais\b|\bhowever\b|\bcependant\b", re.IGNORECASE)
_NEGATION = re.compile(
    r"\b(?:no|not|without|never|lacks?|lacking|none|aucune?|sans|jamais|"
    r"pas\s+(?:de|d['’]|encore|du|des)|n['’](?:ai|a|avons)\s+(?:pas|jamais|aucune?)|"
    r"ne\s+\w+\s+(?:pas|jamais|plus|aucune?))\b",
    re.IGNORECASE,
)


@dataclass
class ScreeningReport:
    text: str                                   # CV text used for scoring
    copied_tokens: int = 0
    copied_spans: int = 0
    structure_detected: bool = False
    evidence_text: str = ""                     # experience / projects / summary text
    declared_text: str = ""                     # skills lists
    notes: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, object]:
        return {
            "copied_tokens": self.copied_tokens,
            "copied_spans": self.copied_spans,
            "structure_detected": self.structure_detected,
            "notes": list(self.notes),
        }


def remove_copied_spans(cv: str, job: str, min_tokens: int = COPY_MIN_TOKENS) -> Tuple[str, int, int]:
    """Remove from the CV every run of >= min_tokens tokens also present in the offer."""
    cv = cv or ""
    cv_tokens = [(m.group(0).lower(), m.start(), m.end()) for m in _TOKEN.finditer(cv)]
    job_tokens = [m.group(0).lower() for m in _TOKEN.finditer(job or "")]
    if len(cv_tokens) < min_tokens or len(job_tokens) < min_tokens:
        return cv, 0, 0
    job_grams = {tuple(job_tokens[i:i + min_tokens]) for i in range(len(job_tokens) - min_tokens + 1)}
    covered = [False] * len(cv_tokens)
    words = [t[0] for t in cv_tokens]
    for i in range(len(words) - min_tokens + 1):
        if tuple(words[i:i + min_tokens]) in job_grams:
            for k in range(i, i + min_tokens):
                covered[k] = True
    if not any(covered):
        return cv, 0, 0
    pieces, cursor, spans, i = [], 0, 0, 0
    while i < len(cv_tokens):
        if covered[i]:
            j = i
            while j + 1 < len(cv_tokens) and covered[j + 1]:
                j += 1
            pieces.append(cv[cursor:cv_tokens[i][1]])
            cursor = cv_tokens[j][2]
            spans += 1
            i = j + 1
        else:
            i += 1
    pieces.append(cv[cursor:])
    return "".join(pieces), sum(covered), spans


def strip_negated(text: str) -> str:
    """Drop the part of each clause that follows a negation cue."""
    out, last = [], 0
    for boundary in list(_CLAUSE_SPLIT.finditer(text or "")) + [None]:
        end = boundary.start() if boundary else len(text or "")
        clause = (text or "")[last:end]
        cue = _NEGATION.search(clause)
        out.append(clause[:cue.start()] if cue else clause)
        if boundary:
            out.append(boundary.group(0))
            last = boundary.end()
    return "".join(out)


def strip_negated_skill_mentions(text: str, mentions_skill) -> str:
    """Like ``strip_negated`` but only drops negated parts that name a skill.

    Used for the similarity components (TF-IDF, embeddings): "No experience
    with Kubernetes" is removed, "Aucune certification formelle" is kept, so a
    CV without negated skills is scored exactly as before.
    """
    out, last = [], 0
    for boundary in list(_CLAUSE_SPLIT.finditer(text or "")) + [None]:
        end = boundary.start() if boundary else len(text or "")
        clause = (text or "")[last:end]
        cue = _NEGATION.search(clause)
        out.append(clause[:cue.start()] if cue and mentions_skill(clause[cue.start():]) else clause)
        if boundary:
            out.append(boundary.group(0))
            last = boundary.end()
    return "".join(out)


def similarity_text(cv: str, job: str, extractor) -> str:
    """CV text given to TF-IDF and embeddings: copied offer text and negated
    skill mentions removed; otherwise identical to the original CV."""
    cleaned = remove_copied_spans(cv, job)[0]
    if not _NEGATION.search(cleaned):
        return cleaned
    return strip_negated_skill_mentions(cleaned, lambda frag: bool(extractor.extract(frag)["hard_skills"]))


def split_declared_evidence(cv: str) -> Tuple[str, str, bool]:
    """Return (declared_text, evidence_text, structure_detected)."""
    declared, evidence = [], []
    current = "evidence"            # text before any heading is treated as summary
    structured = False
    for line in (cv or "").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        kind = _heading_kind(stripped)
        if kind:
            current, structured = kind, True
            continue
        if _INLINE_DECLARED.match(stripped):
            declared.append(stripped.split(":", 1)[1])
            structured = True
            continue
        (declared if current == "declared" else evidence).append(stripped)
    if not structured:
        return "", cv or "", False
    return "\n".join(declared), "\n".join(evidence), True


def screen_cv(cv: str, job: str) -> ScreeningReport:
    cleaned, copied, spans = remove_copied_spans(cv, job)
    declared, evidence, structured = split_declared_evidence(cleaned)
    report = ScreeningReport(text=cleaned, copied_tokens=copied, copied_spans=spans,
                             structure_detected=structured, evidence_text=evidence, declared_text=declared)
    if copied:
        report.notes.append(f"{copied} tokens copied verbatim from the offer were ignored.")
    if not structured:
        report.notes.append("No section heading detected: declared and demonstrated skills cannot be separated.")
    return report


def evidence_insufficient(skill_details: Dict) -> Tuple[bool, str]:
    """Whether the matched skills are too weakly evidenced to support HIRE."""
    evidence = (skill_details or {}).get("evidence") or {}
    if not evidence:
        return False, ""
    if evidence.get("copied_tokens", 0) > 0:
        return True, "part of the CV repeats the offer verbatim"
    matched = evidence.get("matched_hard_count", 0)
    share = evidence.get("demonstrated_share")
    if evidence.get("structure_detected") and matched and share is not None and share < MIN_DEMONSTRATED_SHARE:
        return True, (f"only {evidence.get('demonstrated_count', 0)} of {matched} matched skills are "
                      "supported by the described experience")
    return False, ""
