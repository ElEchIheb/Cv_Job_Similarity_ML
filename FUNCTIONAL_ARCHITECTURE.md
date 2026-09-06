# NeuralHire — Functional Architecture

The platform is one coherent pipeline, not a set of independent pages:

```
Candidate ─┐
           ├─→ Evaluation ─→ [TF-IDF · Semantic · Skills] ─→ Hybrid score
Job ───────┘                              │
                                          ▼
                                  DecisionEngine (single source of truth)
                                          │
                        ┌──────────────────┼──────────────────┐
                     Decision          Confidence          Explanation
                        └──────────────────┼──────────────────┘
                                          ▼
                                 Persisted Evaluation
        ┌──────────┬───────────┬──────────┼──────────┬──────────────┐
      History  Leaderboard   Reports    Bulk     Overview      Quality Center
```

## Entities & relationships (`src/models_db.py`)

- **User** 1─* **Candidate**, 1─* **JobOffer**
- **Candidate** 1─* **CV**, 1─* **MatchResult** — `status` ∈ {NEW, UNDER_REVIEW, SHORTLISTED, INTERVIEW, REJECTED, HIRED}, `is_anonymous`
- **JobOffer** 1─* **MatchResult** — `status` ∈ {OPEN, ON_HOLD, CLOSED}
- **MatchResult** *→1 Candidate, *→1 JobOffer, *→1 CV — the evaluation record
- Relationship rules: one candidate → many evaluations; one job → many candidates/evaluations; the same job is reused across candidates (no duplication).

### MatchResult reproducibility fields
`final_score`, `score_hybrid/semantic/keyword/skill`, `decision` (HIRE|CONSIDER|REJECT), `confidence` (level), `decision_confidence` (uncalibrated 0–1), `strong_fit_threshold`, `potential_fit_threshold`, `model_version`, `evaluation_method`, `weights_json`, `explanation_json`, `created_at`.

## Decision lifecycle (`src/decisioning`)
1. Hybrid score → percentage (0–100).
2. `DecisionEngine.evaluate(pct, config, critical_missing)`:
   - `pct ≥ strong_fit_threshold` → **HIRE** (Strong Fit)
   - `potential_fit_threshold ≤ pct < strong` → **CONSIDER** (Potential Fit)
   - `pct < potential_fit_threshold` → **REJECT** (Low Fit)
3. `decision_confidence` = distance to the nearest threshold, normalised to [0,1]. **Uncalibrated** — not a probability of hire/success.
4. `reason` — a human-readable justification referencing the score, band and any critical missing skills.

**Config validation:** `0 ≤ potential < strong ≤ 100`; rejects NaN, out-of-range, wrong types (incl. bool).

## Threshold semantics
- The **active** configuration lives in the Streamlit session (`frontend/decision_state.py`); Settings edits it (validated) and it governs every **future** evaluation in the session.
- Each persisted evaluation stores the thresholds it was scored with; changing settings later never rewrites history.

## Evaluation lifecycle (`src/matching/service.py`)
`run_evaluation(models, cv, job, model_key, config)` → runs models → DecisionEngine → explainer (same config) → `{result, explanation, recommendations, decision, config}`.
`persist_evaluation(...)` → resolve/reuse Candidate (named → reuse; anonymous → stable `Candidate #YYYY-NNN`), resolve/reuse Job (titled → reuse; untitled → `Untitled Position #YYYY-NNN`), store CV row, insert MatchResult with metadata, commit atomically.

## Model loading
Single loader `load_production_models()` used by both the Streamlit app and the API (lazy/cached). It validates the checkpoint and **fails loudly** if the TF-IDF is unfitted (the fitted-state guard is preserved, never bypassed).

## Ranking / Bulk / Reports
- **Ranking** and **Bulk** call the same `run_match` → same DecisionEngine; ranking sorts deterministically (score desc, then name); identity preserved (CV filename → candidate; shared job per ranking run).
- **Reports** consume the already-computed `result` + `explanation` payload (whose decision is canonical) — no recomputation of the model during PDF generation.

## Overview & Quality Center
- Overview aggregates **persisted** decisions/scores (Hire Rate = HIRE ÷ completed evaluations).
- Quality Center shows **offline benchmark** metrics from `evaluation/results/evaluation_results.json` with explicit provenance; it does not fabricate fairness or domain figures.

## Known limitations
See `FUNCTIONAL_AUDIT.md` §Known limitations.
