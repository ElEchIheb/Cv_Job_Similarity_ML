# NeuralHire — AI Engine Bug Fixes (Logic Layer)

Date: 2026-09-06 · Scope: matching/scoring engine only (no frontend design/motion/3D changes).

Test case used throughout: **Alex Martin** CV vs a **Full Stack Web Developer** job offer
(job requires 11 skills incl. HTML & CSS; candidate lists all 11; experience stated as
`Full Stack Web Developer — TechSolutions, 2023–2026`).

## Summary — before vs after

| Signal | Before (buggy) | After (fixed) |
| --- | --- | --- |
| Years of experience | `Not detected` (→ scored as 0) | `3.0` (detected) |
| Radar — Experience (candidate) | `0%` vs `70%` required → **−70 gap** | `100%` vs `70%` |
| Skill coverage | `9/9 required skills` (HTML/CSS dropped) | `11/11 required skills` |
| Missing skills | `None detected` (but 2 were silently lost) | `None` (all 11 genuinely matched) |
| Radar — Required side | hardcoded `[85,80,70,65,80]` | per-job where derivable + `job_requirements_source` labels |

---

## Bug 1 — Experience extraction failed on explicit date ranges

**Root causes (two):**
1. `SkillExtractor._detect_years_experience` only matched `"N years/yrs/ans"`. It had **no
   date-range parsing at all**, so `"2023–2026"` yielded 0.
2. `parsing.parser.clean_text` scrubs phone numbers with
   `(?<!\w)(?:\+?\d[\d().\-\s]{7,}\d)`, which **also matches `2023-2026`** and deleted compact
   hyphen ranges before any parser could see them. Experience was being detected on
   `clean_text`-processed text, so even a good range parser would have missed hyphen ranges.

`"Not detected"` silently fell back to `0`, and the radar formula
`min(100, candidate_years/required_years*100)` produced exactly `0%` — indistinguishable from a
candidate with confirmed zero experience.

**Fix** (`src/nlp/skill_extractor.py`, `src/explainability/explainer.py`):
- Rewrote `_detect_years_experience` to parse, from **raw text** (bypassing the phone scrubber):
  explicit `N years/ans`; and date ranges with separators `-`, `–`, `—`, `to`, `until`, `au`,
  `à`, `jusqu'à`; open ends `present/current/now/actuel/en cours` resolve to today; English +
  French month names give month-level precision. Durations are **summed across multiple
  entries**. Returns `None` when nothing is parseable.
- Added an honest **`experience_detected`** flag to the extractor payload. A parse failure
  (`years=0, detected=False`) is now distinct from confirmed zero.
- Explainer surfaces this: `experience_fit.candidate_years_detected`,
  `experience_fit.required_years_detected`, `fit_status = "Not detected"` when undetected, and
  `radar_data.experience_detected`. The radar Experience number stays numeric (0.0) for
  backward-compatibility with consumers that divide by 100 (e.g. the PDF radar); the flag lets
  a UI render it as "N/A" instead of a real 0.

> Frontend note (out of scope here, flagged): `radar_data.experience_detected` is now available
> but the web/PDF surfaces still draw the Experience axis as a numeric 0 when undetected. A
> small frontend follow-up should render "N/A" using this flag.

**Regression tests** (`tests/test_skill_extractor.py`): en-dash, hyphen (phone-scrub regression),
present-ended, multiple-entries-summed, explicit-years, and honest-not-detected.

## Bug 2 — Common skills (HTML, CSS) invisible to the dictionary

**Root cause:** `data/datasets/skills_dictionary.json` simply **did not contain `html` or `css`**
(nor `html5`/`css3`). There is **no short-token / stopword filter** dropping them in the
dictionary match path — they were pure blind spots. Because the coverage denominator is
`len(job_hard_skills_extracted)`, unrecognized required skills vanished from **both** the matched
and missing buckets, shrinking `11` → `9`.

**Fix:**
- Added `html`, `css`, `responsive design` to `frontend_frameworks`; aliases `html5→html`,
  `css3→css`, `scss→sass`; bumped `metadata.hard_skill_total` 1039 → 1042.
- Audit note: `restful api→rest api`, `ui→user interface`, `ux→user experience` aliases already
  existed. `sql`, `rest api`, `ci/cd`, `git`, etc. are all present. `ui`/`ux` alias *targets*
  (`user interface`/`user experience`) are not themselves hard-skill entries, so those tokens
  still won't count toward coverage — noted as a lesser, separate gap, not fixed here to avoid
  scope creep.
- Coverage now always reflects the full recognized requirement; every required skill lands in
  exactly one bucket (matched XOR missing).

**Regression tests:** common web skills recognized; and full `N/N` coverage when a CV lists every
required skill verbatim (with a matched/missing partition assertion).

## Bug 3 — Radar "Required" values were fully hardcoded

**Root cause:** `explainer.py` returned a constant `job_requirements = [85, 80, 70, 65, 80]`,
identical for every job — not derived from the selected offer.

**Fix:** each axis is now derived from the job offer **where the data model allows**, and every
axis is tagged in `radar_data.job_requirements_source` as `"job"` (derived) or `"benchmark"`:
- **Domain** — `90` if the JD has a specific (non-generalist) domain, else `50`. *(job-derived)*
- **Soft Skills** — `20 × (soft skills the JD lists)`, capped 100; benchmark `65` if none listed.
  *(job-derived when present)*
- **Experience** — `100` (meeting the stated required years is the bar) when the JD states
  required years; benchmark `70` otherwise. *(job-derived when present)*
- **Technical** (`85`) and **Semantic** (`80`) remain **explicit, labelled benchmarks** — target
  skill-coverage / thematic-alignment levels that the current `JobOffer` model does not capture
  as structured fields, so they cannot honestly be computed from JD text today. They are marked
  `"benchmark"` rather than implying they are specific to the job.

> For the Alex Martin JD (no stated years, no explicit soft-skills section), Experience/Soft
> fall back to benchmarks and only Domain is job-derived — the source labels make this explicit
> instead of silently presenting fixed numbers as job-specific.

## Bug 4 — Score inflation from CV/JD textual similarity (keyword gaming) — FLAGGED, NOT changed

**Investigation (empirical, controlled):** using the production checkpoint
(`models/checkpoints/hybrid.pkl`, weights **tfidf 0.9 / embedding 0.0 / skill 0.1**,
`optimal_threshold 0.04`), two CVs with **identical skills (skill score = 1.000) and identical
substance** were scored against the same JD:

| CV variant | TF-IDF | Skill | **Production hybrid** |
| --- | --- | --- | --- |
| Echo (mirrors JD wording) | 0.991 | 1.000 | **99.2%** |
| Paraphrase (same substance, reworded) | 0.707 | 1.000 | **73.6%** |

A **~25.6-point swing from wording alone.** The component that would recognize semantic
equivalence (embeddings) is weighted **0.0**, so the score is almost entirely keyword overlap —
a genuine, gameable weakness.

**Provenance:** the weights come from `HybridMatcher.optimize_weights` (grid search maximizing
validation AUC) baked into the checkpoint. The degenerate `optimal_threshold = 0.04` (already
known not to drive recruiter decisions — those use the 75/55 DecisionEngine) strongly suggests
this checkpoint overfit a particular synthetic validation split rather than reflecting an intended
production weighting. The documented default is `0.2 / 0.4 / 0.4`.

**Decision required (not made here):** per the ground rules, the production weighting was **not**
changed — it affects every historical and future score. Recommendation for sign-off: re-export
the checkpoint with the documented `0.2/0.4/0.4` split (or re-run `optimize_weights` with
regularization / a held-out test set and a non-degenerate threshold), then re-baseline. This is a
product decision, flagged for the user.

---

## Impact on historical records

Pre-fix `MatchResult` rows produced for similarly-formatted CVs may have **understated**
experience (any CV whose experience was expressed only as a date range → `years=0`, Experience
radar `0%`) and **understated skill coverage** (any job/CV using HTML, CSS, HTML5, CSS3, or SCSS
→ those skills dropped from the coverage denominator). These records were **not** retroactively
recomputed; re-running an affected evaluation now yields the corrected values. Bug 4 does not
change any stored score (weights were left untouched pending sign-off).

## Files changed

- `data/datasets/skills_dictionary.json` — added html/css/responsive design + aliases; count.
- `src/nlp/skill_extractor.py` — date-range experience parser + `experience_detected` flag.
- `src/explainability/explainer.py` — honest experience state + per-job radar requirements.
- `tests/test_skill_extractor.py` — regression tests for Bugs 1 & 2.
