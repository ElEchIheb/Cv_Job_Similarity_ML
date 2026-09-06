# NeuralHire — Known, Approved Deviations from the Streamlit App

The Next.js rebuild is a design/UX reskin with full functional parity. The
following are the **only** intentional behavioral differences from the original
Streamlit app. Each was reviewed and explicitly approved as the correct,
official behavior going forward — they are **not** parity gaps or bugs.

---

## 1. AI Insights uses the non-persisting evaluation path (bug fix)

**Streamlit behavior (old):** `frontend/pages/model_comparison.py` called
`run_match(...)` (which persists) **without a `job_offer_id`**. The persistence
service (`evaluate_and_persist`) raises `ValueError` when asked to persist with
no `job_offer_id`, so the page's per-model `try/except` caught an error for every
method — the comparison crashed on every use.

**Next.js behavior (new, official):** the AI Insights page calls
`POST /ui/compare`, which runs each of the four methods through the canonical
**`run_evaluation`** (no persistence — a model comparison should never write
match records). This produces the side-by-side comparison that was always the
*intended* behavior.

**Status:** intentional deviation. Do not replicate the original crash.

---

## 2. All data is scoped to the logged-in recruiter (product decision)

**Streamlit behavior (old):** the Overview stats, Candidate History, Job Offers,
and Analysis History queried the database with **no recruiter filter** — every
recruiter saw all recruiters' candidates, jobs, and evaluations globally.

**Next.js behavior (new, official):** every data surface is scoped to
`recruiter_id == current_user.id`. A recruiter sees only their own data.

**Applied consistently across every listing surface:**

| Surface | Endpoint | Scoping |
| --- | --- | --- |
| Overview stats | `GET /ui/overview` | candidate/job/match counts + avg all filter `recruiter_id` |
| Candidate History | `GET /ui/candidates` | `filter(recruiter_id == user.id)` |
| Job Offers | `GET /ui/job-offers` | `filter(recruiter_id == user.id)` |
| Analysis History | `GET /ui/matches` | `join(Candidate).filter(recruiter_id == user.id)` |
| Candidate Analysis | `POST /ui/evaluate[/file]` | job lookup + persistence use `recruiter_id == user.id` |
| Talent Leaderboard | `POST /ui/evaluate/file` (per file) | evaluates + persists under the current recruiter; results are computed client-side from those responses, so they are inherently the recruiter's own |
| Mutations | job/candidate PUT/DELETE/toggle | ownership checked via `recruiter_id == user.id` before any write |

**Status:** intentional, approved product decision. Do not restore global
visibility.

---

*Everything else — decision thresholds and labels, score components, skill
matching, job-code format, delete-guards, validation, auth flow — is a faithful
port that calls the same backend logic the Streamlit app used.*
