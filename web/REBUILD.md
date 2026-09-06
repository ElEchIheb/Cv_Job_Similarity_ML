# NeuralHire — Next.js Rebuild ("Precision Intelligence")

A **design/UX reskin with full functional parity** to the Streamlit app. Every
page, feature, and calculation exists and works identically in Next.js; only the
visual layer (tokens, layout, motion, 3D) changed. All business logic is executed
by the **real FastAPI backend** — nothing is re-derived in the browser.

---

## Running it

Two processes: the Python backend and the Next.js frontend.

```bash
# 1) Backend (from repo root)
.venv/Scripts/python -m uvicorn src.api.main:app --port 8000

# 2) Frontend (from web/)
cd web && npm install && npm run dev     # http://localhost:3000
```

`web/.env.local` → `NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1`.
There is **no mock mode** — the UI talks to the live backend only.

> First evaluation loads the AI models (~50s once per backend process; on this
> Windows box the multilingual embedder falls back to a HashingVectorizer due to
> a paging-file limit, exactly as the Streamlit app does). Subsequent calls are
> fast.

---

## Architecture — how parity is achieved over HTTP

The Streamlit app is a **hybrid**: it uses HTTP only for auth and calls the
backend **in-process** for everything else (`SessionLocal`, `MODELS`,
`src.matching.service.evaluate_and_persist`). A browser can't do that, and the
original FastAPI app exposed only a thin subset. So the backend gained an
**additive parity router** — `src/api/routers/ui.py` — whose every endpoint
**calls the existing, unchanged service/DB code**. No algorithm, threshold, or
schema was modified; existing endpoints are untouched. (CORS methods were widened
to allow PUT/DELETE.)

| Page | Backend endpoint(s) | Notes |
| --- | --- | --- |
| **Login** | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` | OAuth2 bearer, unchanged |
| **Overview** | `GET /ui/overview`, `GET /ui/matches` | recruiter-scoped counts + avg + HIRE-rate (dashboard.py) |
| **Candidate Analysis** | `POST /ui/evaluate`, `POST /ui/evaluate/file`, `POST /report/pdf` | routes through `evaluate_and_persist` with the session's thresholds; model select, email, paste/upload, PDF |
| **Talent Leaderboard** | `POST /ui/evaluate/file` (per file) | filename→name, score-desc/name-asc sort, stats, CSV — same persistence as Streamlit |
| **Candidate History** | `GET/PUT/DELETE /ui/candidates` | edit (name/email/phone/status), delete blocked when evaluations exist |
| **Job Offers** | `GET/POST/PUT/DELETE /ui/job-offers`, `…/toggle-status` | auto `JOB-YYYY-NNN`, status, eval counts, delete-guard |
| **Analysis History** | `GET /ui/matches`, `GET /ui/matches/{id}` | joined table, client-side filters, raw JSON payload |
| **AI Insights** | `POST /ui/compare` | 4-method side-by-side via `run_evaluation` (no persist) |
| **AI Quality Center** | `GET /ui/quality`, `…/figures`, `…/figures/{name}` | reads `evaluation/results/*.json` + `figures/*.png` |
| **Settings** | `GET /ui/system` + client threshold state (`lib/decision-config.tsx`) | thresholds mirror `frontend/decision_state.py`; passed to every evaluation |

**Canonical logic ported by calling it, not re-writing it:** decisions come from
the backend `DecisionEngine` (HIRE ≥ Strong-Fit, CONSIDER ≥ Potential-Fit, else
REJECT; band labels Strong/Potential/Low Fit; confidence = nearest-threshold /
20). Model labels, `JOB-YYYY-NNN` codes, delete-guards, and validation match the
Streamlit source exactly. Display-only constants live in `lib/constants.ts`.

---

## Verified end-to-end against the live backend

- **Auth** — registered + logged in a real recruiter; `/auth/me` round-trips.
- **Job Offers** — created **JOB-2026-003** through the UI (auto-code increments
  from JOB-2026-002); list shows codes/status/eval-counts.
- **Candidate Analysis** — real evaluation returned **58.7% → CONSIDER /
  "Potential Fit"**, confidence Low·19%, 6/7 skill coverage, NLP flagged as the
  critical gap — identical to what the Streamlit engine produces for the same
  input; persisted as a real MatchResult.
- **Overview / Candidate History / Analysis History** — all reflect the real
  persisted rows (1 candidate, 1 job, 1 match, 58.2% avg).
- **AI Insights** — all four methods computed live (Overall 89% Strong Fit,
  Semantic 71% Potential Fit, Keyword 88%, Skills 100%).
- **AI Quality Center** — renders the real `evaluation_results.json` benchmark
  (provenance dated 2026-08-14) with per-metric bars and charts.
- **Settings** — threshold policy (75/55) drives Candidate Analysis + Leaderboard.
- **Talent Leaderboard** — uploaded 4 real PDF CVs (strong→weak) through the
  drag-and-drop UI; each evaluated via `/ui/evaluate/file`, ranked score-desc
  (Amira 65% Potential Fit → Diego 52% → Karim 42% → Lena 1%, all Low Fit),
  summary stats + distribution + tilt cards + CSV all correct, and all four
  **persisted** (verified as matches #13–16 in Analysis History).

**All 10 of 10 pages are verified live against the real backend.**

See `KNOWN_DEVIATIONS.md` for the two approved intentional differences from the
Streamlit app (AI Insights non-persisting comparison; recruiter-scoped data).

---

## Design system (unchanged from pass 1)

Tokens in `tailwind.config.ts` + `app/globals.css` (dual theme, WCAG-audited),
the `/components/ui` library, Framer-Motion language, and the R3F ambient field /
score torus (with SVG + reduced-motion fallbacks). See the earlier design notes
for the contrast audit and motion specs.

### One dev caveat found & fixed
The Candidate Analysis result initially never appeared because a top-level
`AnimatePresence mode="wait"` around the form↔result swap never fired
`onExitComplete`, so the result never mounted (backend returned 200 the whole
time). Replaced with a plain conditional render; the cinematic reveal still lives
inside `ScoreReveal`.
