# NeuralHire — Functional Audit & Repair

_Full functional audit of the platform (backend, AI engine, persistence, API,
frontend workflows) with the fixes implemented. This is a functional/data
consistency effort — the AI models, weights, thresholds-of-training, dataset and
evaluation methodology were **not** altered._

---

## 1. Current architecture (as traced)

- **Frontend:** Streamlit single-page app (`frontend/app.py`) with custom routing. It loads the AI models **in-process** via `src.models.model_loader.load_production_models()` and evaluates through a local `run_match()` — it uses the FastAPI backend **only for auth**.
- **Backend API:** FastAPI (`src/api/main.py`) exposes `/match`, `/rank`, `/batch`, `/report/pdf`, CRUD for candidates/jobs/matches. Same model loader (lazy, cached). Endpoints are auth-gated.
- **AI engine:** `HybridMatcher` (`src/fusion/hybrid_scorer.py`) = weighted blend of `TFIDFMatcher`, `EmbeddingMatcher`, `SkillMatcher`. Explainability in `src/explainability/explainer.py`.
- **Persistence:** SQLAlchemy models in `src/models_db.py` on SQLite (`data/neuralhire.db`). Entities: User, Candidate, CV, JobOffer, MatchResult, Skill.
- **Checkpoint:** `models/checkpoints/hybrid.pkl` (only the fitted TF-IDF is persisted; embedding/skill re-instantiated at load).

## 2–8. Flows (candidate / job / evaluation / ranking / bulk / report / threshold / persistence / model-loading)
See `FUNCTIONAL_ARCHITECTURE.md` for the repaired lifecycles. Below are the defects found in each.

## 9. Existing bugs (evidence-based)

| # | Severity | Finding (traced in code + live DB) |
|---|---|---|
| B1 | **Critical** | **Four disagreeing decision paths.** Persisted `decision` came from `HybridMatcher.predict()['label']` using the checkpoint's `optimal_threshold = **0.04**`; the explainer computed its own bands around a (never-supplied, so default) `0.60`; the UI badges used fixed 75/55; the Settings sliders fed nothing. |
| B2 | **Critical** | Because of the 0.04 threshold, **any score ≥ 4% was persisted as HIRE** — live DB showed 9.4%→HIRE, 45.8%→HIRE, only 0.0→REJECT (25 of 27 rows HIRE). |
| B3 | **Critical** | **Settings thresholds were cosmetic** — the sliders never influenced any evaluation. |
| B4 | High | **Candidate/Job duplication.** `run_match()` created a **new** Candidate and JobOffer on **every** evaluation. Live DB: 25× "Anonymous Candidate", 26× "Unnamed Job Offer", 27 candidates / 27 jobs / 27 matches (1:1:1). |
| B5 | High | **CVs never persisted** (`cvs` table empty); `MatchResult.cv_id` always NULL. |
| B6 | High | **No reproducibility metadata** — thresholds, confidence, model version, weights, evaluation method were not stored; component score columns (`score_semantic/keyword/skill`) were NULL from the frontend path. |
| B7 | High | **Confidence mislabelled.** Shown as a bare progress bar with no statement that it is an uncalibrated distance-from-threshold value, risking a "probability of hire" reading. |
| B8 | Medium | **Ranking / Bulk each re-derived decisions locally** (their own 75/55 copies) and ranking discarded the filename-derived candidate identity (called `run_match` with no name/title). Tie-ordering was non-deterministic. |
| B9 | Medium | **AI Quality Center presented offline benchmark numbers as if live**; latency label ambiguous; "Subgroup **Fairness**" implied protected-attribute fairness though only seniority/domain segments exist; error-analysis printed "Dominant domain: N/A" when absent. |
| B10 | Medium | **Status was hardcoded "ACTIVE"** for every candidate and job — no real recruitment/position lifecycle. |
| B11 | Low | French string leaked into the English skill-coverage label. |

## 9b. Data inconsistencies / missing relationships / risky assumptions
- Same (candidate, job) recomputed produced a different persisted decision than the badge shown → **inconsistent across pages**.
- Missing 1→many relationships in practice (each eval spawned fresh entities instead of reusing).
- Risky: relying on a serialized model's tuned classification threshold as the recruiter decision policy.

## 10. Recommended fixes → **implemented**

1. **Central DecisionEngine** (`src/decisioning/decision_engine.py`) — the single source of truth: `classify`, `decision_confidence`, `evaluate`, strict `DecisionConfig` validation. Semantics: `≥ strong → HIRE`, `≥ potential → CONSIDER`, else `REJECT`. Default 75 / 55.
2. **Explainer routed through the engine** — `MatchingExplainer.explain(..., config)` now derives `hiring_recommendation.decision`, `verdict` and confidence from the DecisionEngine, so the API and the frontend produce the **same** decision.
3. **Canonical matching service** (`src/matching/service.py`) — `run_evaluation` + `persist_evaluation` + `evaluate_and_persist`: one path that evaluates, decides, de-duplicates Candidate/Job, stores the CV document, and persists full reproducibility metadata atomically.
4. **Frontend `run_match` rewritten** to call the service with the session's active config; **Ranking** and **Bulk** now use the canonical decision, preserve identity, and rank deterministically (score desc, then name).
5. **Settings now controls evaluations** — sliders write a validated `DecisionConfig` to session state (`frontend/decision_state.py`); Candidate Analysis / Leaderboard / Bulk all read it. Session-scoped by design, made explicit in the UI.
6. **Schema + safe migration** (`src/db_maintenance.py`) — additive `ADD COLUMN` for metadata + status; a timestamped DB backup; and a one-time **backfill** that re-derives legacy decisions from their *unchanged* scores using the canonical policy (tagged `legacy-recompute`). Historical scores are never altered; new evaluations keep the thresholds they were scored with.
7. **AI Quality Center honesty** — provenance banner (offline benchmark + timestamp), latency relabelled as offline per-pair inference, "Subgroup Performance" with an explicit note that no protected-attribute fairness is claimed, and fabricated "dominant domain N/A" removed.
8. **Confidence semantics** stated in the UI as *uncalibrated decision confidence — not a probability of hire*.
9. **Real status** surfaced for candidates (NEW/…/HIRED) and jobs (OPEN/ON_HOLD/CLOSED).

## 11. Verification
- `pytest tests/test_decision_engine.py tests/test_matching_consistency.py` → **34 passed** (boundaries, invalid configs, determinism, explainer==engine, dedup, stable anonymous IDs, metadata).
- Live DB backfill re-ran: decisions now match the 75/55 policy (9.4%→REJECT, 45.8%→REJECT, 93.9%→HIRE); distribution CONSIDER 17 / HIRE 4 / REJECT 6.
- Pre-existing, unrelated failures (auth-gated API tests without tokens; a test that builds an unfitted `HybridMatcher()`; auth-env tests) are documented in the final report and were **not** introduced by this work.

## Known limitations
- Full app launch in this environment segfaults during the `torch`/`sentence-transformers` import (native crash, pre-existing) — so live end-to-end screenshotting of authenticated pages could not be performed here. The decision/persistence layer was verified via unit tests and direct DB inspection instead.
- Candidate recruitment status is displayed but not yet editable from the UI (no page redesign was in scope).
- AI Quality Center metrics remain sourced from the offline evaluation file (now clearly labelled); they are not recomputed live.
