# NeuralHire Data Redesign Audit

## 1. Current State
### `src/models_db.py`
- `JobOffer`: created dynamically on every evaluation, deduped strictly by `title` and `recruiter_id`. Uses auto-incrementing integers (`id`) for primary key. No unique `job_code` exists.
- `Candidate`: created dynamically on every evaluation, deduped strictly by `full_name` (case-insensitive) and `recruiter_id`. Fallback to an anonymous name. `email` column exists but is not used as the dedup key.
- `MatchResult`: represents a single evaluation/application. Links candidate, job, and cv.

### `src/matching/service.py`
- `_resolve_job` searches by `title`. If not found, creates a new `JobOffer`.
- `_resolve_candidate` searches by `name`. If not found, creates a new `Candidate`.
- `evaluate_and_persist` auto-generates jobs and candidates.

### `frontend/pages/job_offers.py`
- Displays active job offers.
- No UI exists to create ("Add Job Offer"), edit, or delete jobs.
- Displays evaluated counts based on linked `MatchResult` rows.

### `frontend/pages/single_match.py` & `ranking.py`
- Allows arbitrary text input for `job_title` and `job_text`.

## 2. Target State
### Schema Changes (`src/models_db.py`)
- `JobOffer`: add `job_code` (`String`, `unique=True`, `index=True`, `nullable=False`).
- `Candidate`: deduplicate by `email` (`unique=True`). Keep `is_anonymous` behavior if email is missing.

### Application Flow Changes
- **Job Offers**: Add an "Add Job Offer" form to `job_offers.py` to create jobs. Add Edit/Delete/Toggle Status capabilities. Job codes generated here (e.g. `JOB-2026-001`).
- **Candidate Analysis**: Remove job creation from `_resolve_job`. `single_match.py` must use a selectbox/dropdown referencing existing active `JobOffer` records.
- **Candidates**: Require `candidate_email` in the frontend (or leave blank for anonymous). `_resolve_candidate` deduplicates by `email`.
- **Analysis History**: Add filters for `Job Offer Code`, `Job Offer Name`, and `Candidate Email`.
- **Bulk Evaluation**: Completely removed from `app.py` and `frontend/pages/batch_analysis.py`.

## 3. Migration Plan (`src/db_maintenance.py`)
1. Add `job_code` column to `job_offers`.
2. Backfill existing jobs with unique `job_code`.
3. Merge duplicate jobs (by title/description similarity or just title).
4. Merge duplicate candidates by `email` (where `email` is not null). Re-point `MatchResult` and `CV` rows.
5. Delete orphaned merged records.
6. Idempotent design ensuring no data loss.
