"""
src/ai/prompts/deep_analysis_prompt.py

Prompt template for Layer 2 (LLM qualitative reasoning) of NeuralHire.

Kept deliberately separate from application/service code so it is a reviewable
artifact for the thesis defense and can be iterated on without touching the
Ollama client or the API. Nothing here calls a model — this module only builds
the system prompt, the JSON output contract, and the grounded user prompt from
the already-computed statistical results.

Design principles (see LLM_LAYER.md):
  * GROUND, don't re-derive — the model is handed the statistical engine's
    scores/skills/experience and asked to *interpret*, not to re-score.
  * NO competing number — the LLM must never emit its own compatibility %.
  * FAIRNESS — explicit instruction to ignore protected characteristics.
  * STRICT JSON — a single structured object matching RESPONSE_SCHEMA.
"""
from __future__ import annotations

import json
from typing import Dict, List

# ── Output contract ───────────────────────────────────────────────────────────
# The exact JSON shape the model must return. Also used by the service to
# validate the parsed response (presence + types of the top-level keys).
RESPONSE_SCHEMA: Dict[str, object] = {
    "career_trajectory": {
        "summary": "string — 2-4 sentence narrative of the candidate's career progression",
        "seniority_signal": "string — one of: junior | mid-level | senior | lead | unclear",
        "progression": "string — growth pattern / relevance of past roles to THIS role",
    },
    "red_flags": [
        {
            "issue": "string — a concrete concern the statistical layer cannot catch",
            "severity": "string — one of: low | medium | high",
            "evidence": "string — what in the CV/JD/scores suggests it (or 'not evidenced')",
        }
    ],
    "recommendations": [
        {
            "recommendation": "string — specific to THIS candidate and THIS job",
            "rationale": "string — why it matters here",
        }
    ],
    "fit_justification": "string — one recruiter-readable paragraph synthesising the "
                         "statistical score with the qualitative read, in plain language",
    "interview_questions": [
        {
            "question": "string — tailored to a specific gap or strength found",
            "targets": "string — the gap/strength this probes",
        }
    ],
}

# Top-level keys the service requires to consider a response valid.
REQUIRED_KEYS: List[str] = [
    "career_trajectory",
    "red_flags",
    "recommendations",
    "fit_justification",
    "interview_questions",
]

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a senior technical recruiter assistant embedded in an AI hiring platform. \
You provide a QUALITATIVE second opinion that complements an existing statistical matching engine.

Your role and hard constraints:
1. GROUNDING: Base every statement strictly on the CV text, the job description, and the \
pre-computed statistical results you are given. Do NOT invent skills, employers, dates, \
or achievements that are not present in the source text. If something is not evidenced, say so.
2. NO COMPETING SCORE: The statistical engine already produced the official compatibility \
percentage and HIRE/CONSIDER/REJECT decision. You MUST NOT produce your own percentage or \
overturn the decision. If your qualitative read diverges from the number, express that only as \
a note inside "red_flags" or "fit_justification" — never as a competing score.
3. FAIRNESS (non-negotiable): Do NOT infer, mention, or base any judgement on protected or \
sensitive characteristics — age, gender, ethnicity, nationality, religion, marital status, \
disability, sexual orientation, or photographs. Ignore any such signals even if they are \
inferable from the CV. Assess only professional qualifications, skills, and experience.
4. TONE: Professional, concise, HR-appropriate, and specific. Avoid generic boilerplate; \
tie observations to this candidate and this role.
5. RED FLAGS: Never describe a matched skill or an otherwise positive qualification as a red \
flag. If no concrete concern is evidenced, return one low-severity item saying "No material \
red flag evidenced" and cite the relevant CV/JD evidence. Do not copy schema-placeholder text.
6. OUTPUT: Return ONLY a single valid JSON object matching the requested schema. Before sending, \
check that it has all five keys: career_trajectory, red_flags, recommendations, \
fit_justification, and interview_questions. No markdown, no code fences, no commentary before \
or after the JSON. The schema's explanatory phrases (for example, "string — ..." and \
"growth pattern / relevance") are NOT values: replace every field with an actual, grounded \
statement. Every interview question must name a CV/JD skill, responsibility, or evidenced gap."""


# ── User prompt builder ───────────────────────────────────────────────────────
def _fmt_list(items: List[str], empty: str = "none") -> str:
    items = [str(i) for i in (items or []) if str(i).strip()]
    return ", ".join(items) if items else empty


def _truncate(text: str, limit: int) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + " …[truncated]"


def build_user_prompt(context: Dict[str, object], *, cv_char_limit: int = 6000,
                      job_char_limit: int = 4000) -> str:
    """Assemble the grounded user prompt from the statistical engine's output.

    `context` is produced by llm_reasoning.build_context(). Long CV/JD text is
    truncated to keep the prompt within a small local model's context window.
    """
    stat = context.get("statistical", {})  # type: ignore[assignment]
    skills = context.get("skills", {})      # type: ignore[assignment]
    exp = context.get("experience", {})     # type: ignore[assignment]

    schema_str = json.dumps(RESPONSE_SCHEMA, indent=2, ensure_ascii=False)

    return f"""Evaluate the following candidate for the target role, then return the JSON object.

=== PRE-COMPUTED STATISTICAL RESULTS (authoritative — do not recompute) ===
Overall compatibility score: {stat.get('percentage', 'n/a')}%
Decision: {stat.get('decision', 'n/a')} ({stat.get('band_label', '')})
Component scores (0-1): keyword/TF-IDF={stat.get('keyword', 'n/a')}, \
semantic/embedding={stat.get('semantic', 'n/a')}, skills={stat.get('skill', 'n/a')}
Matched skills: {_fmt_list(skills.get('matched', []))}
Missing skills: {_fmt_list(skills.get('missing', []))}
Priority (critical) missing skills: {_fmt_list(skills.get('critical_missing', []))}
Skill coverage: {skills.get('coverage', 'n/a')}
Detected years of experience: {exp.get('years', 'n/a')} \
(detected={exp.get('detected', 'n/a')}; role expects ~{exp.get('required_years', 'n/a')} yrs)
Education level: {exp.get('education_level', 'n/a')}

=== JOB DESCRIPTION ===
{_truncate(str(context.get('job_text', '')), job_char_limit)}

=== CANDIDATE CV ===
{_truncate(str(context.get('cv_text', '')), cv_char_limit)}

=== TASK ===
Produce a qualitative deep analysis. Return ONLY a JSON object with exactly these keys \
and shapes (arrays may have 2-5 items each; keep every string concise):

{schema_str}

Remember: ground everything in the text above, do not output any compatibility percentage \
of your own, and never reference protected characteristics."""
