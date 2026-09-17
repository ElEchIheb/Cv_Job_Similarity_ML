# JobTest — Exhaustive Project Report (PFE Thesis Basis)

> **Nature of this document.** This is a from-scratch, code-grounded audit of the
> entire repository at `d:\education\pfe\pfe_ai`. Every claim below was checked
> against the actual source, configuration, dataset, checkpoint, or test output —
> not against memory or prior chat sessions. Where the repository's own older
> documentation contradicts the code, this report follows the **code** and flags
> the discrepancy. Where something is genuinely undocumented or could not be
> verified, that is stated explicitly rather than guessed.
>
> The project was renamed from **NeuralHire** to **JobTest** (commit `5207195`).
> The rename was completed afterwards across source comments, the browser storage
> keys, the development database file name (`data/jobtest.db`), the deprecated
> Streamlit prototype and the project documentation. Two traces are kept on
> purpose: the `LEGACY_*` constants in `web/lib` that migrate a returning
> visitor'''s old localStorage keys once, and the rows already written inside the
> development SQLite file. Older sections of this report may still use the former
> name; both refer to the same platform.

---

## Table of contents

1. Project overview
2. Architecture overview
3. Backend technologies — full inventory
4. Frontend technologies — full inventory
5. AI/ML technologies — full inventory (the core)
6. DevOps & engineering practices
7. Cybersecurity
8. Cloud hosting / deployment
9. Data model
10. Backend API surface
11. Conception & design methodology
12. Full platform workflow (step-by-step)
13. Known limitations (consolidated)
14. Glossary
- Appendix A: Repository file map
- Appendix B: Document-vs-code discrepancies found during the audit

---

## 1. Project overview

### 1.1 What the platform is

JobTest is an **AI-powered recruitment / talent-intelligence platform** that
matches candidate CVs against job descriptions and returns an explainable
compatibility score, a hire recommendation (**HIRE / CONSIDER / REJECT**), a skill
breakdown, a competency radar, actionable up-skilling recommendations, a
downloadable PDF report, and — optionally — a qualitative "deep analysis" written
by a local Large Language Model.

The intended user is a **recruiter / HR specialist**. The secondary subject is the
**candidate**, whose CV (PDF/DOCX or pasted text) is parsed and evaluated. A third
implicit actor is the **administrator / QA engineer** who runs the offline model
benchmark and tunes decision thresholds (`TECHNICAL_DOCUMENTATION.md §1`).

### 1.2 The core problem

Manual CV screening is slow, subjective, and prone to cognitive bias; naïve
keyword filtering misses semantically equivalent phrasing. JobTest addresses this
with a **hybrid statistical matching engine** (keyword + semantic + skills) fused
into one score, wrapped in an **explainability layer** and a **canonical decision
engine** so that the same (candidate, job, threshold configuration) always yields
the same, reproducible verdict.

### 1.3 End-to-end user workflow (as implemented)

1. Recruiter registers / logs in (JWT-based auth).
2. Recruiter creates a **Job Offer** (title, description, required skills; the
   system assigns a `JOB-YYYY-NNN` code and an `OPEN` status).
3. Recruiter opens **Candidate Analysis**, picks the target job, optionally names
   the candidate, and pastes CV text or uploads a PDF/DOCX.
4. The **Layer-1 statistical engine** parses the CV, extracts skills, computes
   TF-IDF / semantic / skill sub-scores, fuses them, and the **DecisionEngine**
   classifies the percentage into HIRE/CONSIDER/REJECT using the active
   thresholds. The evaluation is **persisted** as a `MatchResult`.
5. The UI renders the score (animated ring/torus), the competency radar, a skill
   constellation, gap analysis, and recommendations.
6. Separately and **after** the score renders, the **Layer-2 LLM** ("AI Deep
   Analysis") produces a narrative career read, red flags, tailored interview
   questions, and a plain-language justification — grounded on Layer 1's numbers.
7. Recruiter can export a **7-section PDF report**, rank many candidates at once
   on the **Talent Leaderboard**, review history, compare models on **AI
   Insights**, and inspect the offline benchmark on the **AI Quality Center**.

### 1.4 Brief project history

- **Original prototype**: a Streamlit dashboard (`frontend/`) that loaded the AI
  models in-process and used the FastAPI backend only for auth. Documented in
  `TECHNICAL_DOCUMENTATION.md` and `DESIGN_AUDIT.md`. This app is now
  **deprecated** (`README.md`; `pytest.ini` excludes `frontend/` from tests).
- **Redesign**: a full **Next.js (App Router) rebuild** in `web/` — a "Precision
  Intelligence" reskin with **full functional parity**, achieved by adding an
  additive `/api/v1/ui` FastAPI router that exposes the same in-process service
  logic over HTTP (`web/REBUILD.md`).
- **Iterative hardening**: an AI-engine bug-fix pass (`BUGFIXES.md`), the
  additive **Layer-2 LLM reasoning** layer (`LLM_LAYER.md`), a benchmark-integrity
  overhaul, and a security audit (`SECURITY_AUDIT.md`).
- **Name variants used during development**: "CV Job Similarity ML" (initial
  commit), "NeuralHire", "JobTest AI Platform". Current name: **JobTest**.

---

## 2. Architecture overview

### 2.1 System diagram in words

```
┌──────────────────────────────┐         ┌──────────────────────────────────────┐
│  Next.js frontend (web/)      │  HTTPS  │  FastAPI backend (src/api)            │
│  React 18 + App Router        │ ──────► │  - /api/v1/auth   (OAuth2 + JWT)      │
│  Tailwind + Framer Motion     │  JSON / │  - /api/v1/ui/*   (parity router)    │
│  R3F/three.js 3D              │  form   │  - /api/v1/match, /rank, /report/pdf │
└──────────────────────────────┘         └───────────────┬──────────────────────┘
                                                          │ in-process calls
                          ┌───────────────────────────────┼───────────────────────────────┐
                          ▼                                ▼                               ▼
              ┌────────────────────┐        ┌──────────────────────────┐     ┌──────────────────────┐
              │ Layer 1 (statistical)│      │ DecisionEngine            │     │ SQLAlchemy ORM        │
              │ TFIDFMatcher         │      │ (single source of truth   │     │ SQLite (default) /    │
              │ EmbeddingMatcher     │─────►│  for HIRE/CONSIDER/REJECT)│     │ Postgres (docker)     │
              │ SkillMatcher         │      └──────────────────────────┘     │ Users/Candidates/CVs/ │
              │ HybridMatcher (fuse) │                                        │ JobOffers/MatchResults│
              │ Explainer + Recs     │                                        └──────────────────────┘
              └──────────┬───────────┘
                         │ structured results (no re-scoring)
                         ▼
              ┌────────────────────────────┐   HTTP    ┌───────────────────────┐
              │ Layer 2 (LLM reasoning)     │ ────────► │ Local Ollama server    │
              │ src/ai/llm_reasoning.py     │           │ qwen2.5:1.5b (default) │
              └────────────────────────────┘           └───────────────────────┘
```

### 2.2 The additive `/ui` parity router — why it exists

The Streamlit app was a **hybrid**: it imported the model loader and matching
service *in-process* and only used HTTP for auth. A browser cannot do that, and the
original FastAPI app exposed only a thin subset of operations. Rather than
re-implement business logic in JavaScript, the backend gained an **additive
router** `src/api/routers/ui.py` (`/api/v1/ui/*`) whose every endpoint **calls the
existing, unchanged service/DB code** (`evaluate_and_persist`, `run_evaluation`,
the same SQLAlchemy models, the same `DecisionEngine`). No algorithm, threshold, or
schema is redefined there (module docstring; `web/REBUILD.md`). This is how the
Next.js app reaches parity over HTTP.

### 2.3 Deployment topology (honest status)

- **What is in the repository:** a `docker-compose.yml` defining three services —
  `db` (Postgres 16), `api` (uvicorn on 8000), and `frontend` (**the legacy
  Streamlit app** on 8501) — plus `Dockerfile.api` and `Dockerfile.frontend`
  (both `python:3.11-slim`, both installing CPU-only Torch + `requirements.txt`).
- **What is NOT in the repository:** there is **no Azure VM configuration, no
  Vercel configuration (`vercel.json`), and no Dockerfile for the Next.js app**.
  The "Azure VM (backend + Ollama + DB) + Vercel (frontend)" split described as
  the deployment goal is a **stated plan, not evidenced by any file on disk**. The
  only concrete hardware profile in the repo is the LLM verification machine in
  `LLM_LAYER.md` (**7.75 GB RAM, 4 logical CPUs, ~1.96 GB free RAM, CPU-only**).
  The Docker compose that *does* exist wires the **Streamlit** frontend, not the
  Next.js app — so the shipped container topology and the intended production
  topology diverge, and this is worth stating plainly in the thesis rather than
  presenting the Azure/Vercel split as if it were configured in code.

---

## 3. Backend technologies — full inventory

### 3.1 Runtime & framework

- **Language/runtime:** Python. `HowToRun.txt` recommends **3.10+ (3.11
  preferred)**; `Dockerfile.api` pins **python:3.11-slim**. `PROJECT_REPORT.md`
  notes 3.13 requires `TOKENIZERS_PARALLELISM=false`; the local dev machine in
  this audit runs Python 3.13 (verified from `C:\Python313`).
- **Web framework:** **FastAPI ≥ 0.115.0** on **Uvicorn[standard] ≥ 0.32.0**
  (ASGI). App version string is `"2.0.0"` (`src/api/main.py`), docs at
  `/api/v1/docs`, OpenAPI at `/api/v1/openapi.json`.

### 3.2 Declared dependencies (`requirements.txt`, exact)

| Package | Constraint | Used for |
|---|---|---|
| fastapi | ≥0.115.0 | REST API |
| uvicorn[standard] | ≥0.32.0 | ASGI server |
| python-multipart | ≥0.0.12 | file-upload form parsing |
| httpx | ≥0.28.0 | HTTP client (Ollama calls; TestClient) |
| pandas | ≥2.2.0 | dataset/eval dataframes |
| numpy | ≥2.1.0 | vector math |
| scikit-learn | **==1.8.0** (pinned) | TF-IDF, HashingVectorizer, metrics |
| scipy | ≥1.14.0 | sparse `hstack`, `chi2` (McNemar) |
| matplotlib | ≥3.9.0 | eval figures + PDF charts |
| seaborn | ≥0.13.0 | eval figures |
| streamlit | ≥1.41.0 | **legacy** frontend only |
| pdfplumber | ≥0.11.0 | primary PDF text extraction |
| PyPDF2 | ≥3.0.0 | PDF fallback extraction |
| python-docx | ≥1.1.0 | DOCX extraction |
| spacy | ≥3.8.0 | optional NER / lemmatisation |
| sentence-transformers | ≥3.2.0 | semantic embeddings |
| joblib | ≥1.4.0 | TF-IDF (de)serialisation |
| pytest | ≥8.3.0 | tests |
| reportlab | ≥4.2.0 | PDF report generation |
| python-dotenv | ≥1.0.0 | `.env` loading |
| Pillow | ≥11.0.0 | image handling (reportlab/matplotlib) |
| SQLAlchemy | ≥2.0.0 | ORM |
| python-jose[cryptography] | ≥3.3.0 | JWT encode/decode (HS256) |
| bcrypt | **==3.2.2** (pinned) | password hashing (via passlib) |
| passlib | ≥1.7.4 | password-hash context |
| psycopg2-binary | ≥2.9.9 | Postgres driver |
| alembic | ≥1.13.1 | migrations (barely used — see §6) |

> **Repo-hygiene defect (real, worth noting):** the last two lines of
> `requirements.txt` are a corrupted, space-separated duplicate
> `b c r y p t = = 3 . 2 . 2` followed by a stray blank line. `pip` will fail to
> parse that token as written; it should be removed. Torch is **not** in
> `requirements.txt` — it is installed separately (CPU wheels) inside the
> Dockerfiles; locally it arrives transitively via `sentence-transformers`.

### 3.3 `src/` folder structure (one line each)

| Path | Purpose |
|---|---|
| `src/config.py` | Pydantic-settings config resolved from env/`.env` |
| `src/database.py` | SQLAlchemy engine/session, SQLite pragma, `get_db()` |
| `src/models_db.py` | ORM entities: User, Candidate, CV, JobOffer, MatchResult, Skill + link tables |
| `src/db_maintenance.py` | backup + additive `ensure_schema` + legacy backfill + dedup migration |
| `src/logging_config.py` | structured logging + per-request id |
| `src/security/auth.py` | password hashing, JWT create/verify, `get_current_user` |
| `src/api/main.py` | FastAPI app factory, core endpoints, rate limiter, CORS, lazy model cache |
| `src/api/routers/auth.py` | `/api/v1/auth` register/login/me |
| `src/api/routers/ui.py` | additive `/api/v1/ui/*` parity router |
| `src/parsing/parser.py` | PDF/DOCX extraction, `clean_text`, tokeniser, `segment_cv` |
| `src/parsing/preprocessor.py` | memoised batch text preprocessor |
| `src/nlp/skill_extractor.py` | hybrid skill extraction + experience/education/domain detection |
| `src/models/base_model.py` | abstract matcher + `evaluate` metric bundle |
| `src/models/tfidf_model.py` | `TFIDFMatcher` |
| `src/models/embedding_model.py` | `EmbeddingMatcher` + HashingVectorizer fallback |
| `src/models/skill_matcher.py` | `SkillMatcher` (overlap scoring + gaps) |
| `src/models/model_loader.py` | `load_production_models()` (checkpoint + services) |
| `src/fusion/hybrid_scorer.py` | `HybridMatcher` (weighted fusion, weight/threshold tuning, CV) |
| `src/decisioning/decision_engine.py` | canonical `DecisionEngine` + `DecisionConfig` |
| `src/explainability/explainer.py` | `MatchingExplainer` + `RecommendationEngine` |
| `src/matching/service.py` | `run_evaluation` / `persist_evaluation` / `evaluate_and_persist` |
| `src/reporting/pdf_generator.py` | `MatchReportPDF` (7-section reportlab report) |
| `src/evaluation/evaluator.py` | `EvaluationSuite` (splits, calibration, metrics, figures) |
| `src/ai/llm_reasoning.py` | Layer-2 Ollama client, JSON validation, consistency guard |
| `src/ai/prompts/deep_analysis_prompt.py` | Layer-2 system prompt, schema, grounded user prompt |

### 3.4 Configuration / environment variables (`src/config.py`, `.env.example`)

| Variable | Default (code) | Controls |
|---|---|---|
| `ALLOWED_ORIGINS` | `localhost:8501,3000,3001,3002` | CORS allow-list |
| `REQUEST_LIMIT_PER_MINUTE` | `60` | in-memory per-IP rate limit |
| `JWT_SECRET_KEY` | **random per-process** if unset (+ warning) | JWT signing secret |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | token lifetime |
| `EMBEDDING_MODEL_EN` | **`all-mpnet-base-v2`** | English embedding model |
| `EMBEDDING_MODEL_ML` | `paraphrase-multilingual-mpnet-base-v2` | multilingual embedding model |
| `MATCH_THRESHOLD` | `0.60` | threshold for single non-hybrid model API label |
| `LLM_ENABLED` | `true` | master switch for Layer 2 |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server |
| `OLLAMA_MODEL` | `qwen2.5:1.5b` | Layer-2 model tag |
| `OLLAMA_TIMEOUT` | `120` (s) | generation timeout |
| `OLLAMA_CONNECT_TIMEOUT` | `3` (s) | health/connect timeout |
| `LOG_LEVEL` | `INFO` | logging level |
| `DATABASE_URL` | `sqlite:///…/data/jobtest.db` | DB connection (Postgres in docker) |

> Note: `config.py`'s default `EMBEDDING_MODEL_EN` is **`all-mpnet-base-v2`**,
> which overrides the stale docstring in `embedding_model.py` that claims
> `all-MiniLM-L6-v2` is the default. `.env.example` also sets `all-mpnet-base-v2`.

### 3.5 Startup & background behaviour

- **Lazy model loading.** `src/api/main.py::_get_services()` loads the production
  models on the **first request only**, behind a thread-safe double-checked lock
  (`_services_lock`). Both the core routes and the `/ui` router share this single
  cache (`ui.py::_services()` imports `_get_services`).
- **Additive schema migration at startup.** `create_app()` calls
  `Base.metadata.create_all` then `db_maintenance.ensure_schema(engine)` — an
  idempotent `ALTER TABLE ADD COLUMN` pass that adds newly-introduced columns
  (e.g. `match_results.llm_analysis_json`) without a destructive recreate. The API
  startup deliberately does **not** run the legacy backfill/dedup (those live in
  `run_maintenance` / `run_data_redesign_migration`, invoked from the Streamlit
  maintenance path, not the API).
- **Request middleware.** Every request gets a request-id header
  (`X-Request-ID`), a timing header (`X-Process-Time-ms`), rate limiting, and
  structured logging. Global + per-type exception handlers return JSON errors.
- **SQLite pragma.** `PRAGMA foreign_keys=ON` is set on every SQLite connection
  (`database.py`).

---

## 4. Frontend technologies — full inventory

### 4.1 Stack (`web/package.json`)

- **Next.js `^14.2.35`** (App Router), **React 18.3.1**, **TypeScript 5.6.3**.
- **Tailwind CSS 3.4.14** (+ autoprefixer, postcss 8.4.47).
- **Framer Motion 11.11.17** — the primary motion system.
- **GSAP 3.12.5** — present as a dependency (declared), though the shipped motion
  is overwhelmingly Framer-Motion-based.
- **three.js 0.169.0** + **@react-three/fiber 8.17.10** + **@react-three/drei
  9.114.3** — 3D (neural field, score torus).
- **lucide-react 0.454.0** — icon set.
- **clsx 2.1.1** + **tailwind-merge 2.5.4** — the `cn()` class helper.
- No chart library (visx/D3/Recharts): all charts are **hand-built SVG** (radar,
  skill constellation, band strips, progress ring) or backend-rendered PNGs
  (Quality Center figures).
- **State management:** plain React context — `ThemeProvider`, `ToastProvider`,
  `DecisionConfigProvider` (`web/app/providers.tsx`). No Redux/Zustand. Server data
  is fetched imperatively via `web/lib/api/client.ts` (a thin `fetch` wrapper);
  there is **no mock mode** — the UI talks only to the live backend
  (`web/.env.local` → `NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1`).
- Auth token is stored in `localStorage` under `jobtest-token`; theme under
  `jobtest-theme`; decision thresholds under `jobtest-decision-config`. The former
  `neuralhire-*` keys are migrated once on read, then removed.

### 4.2 Route inventory (App Router)

`web/app/layout.tsx` is the root (theme-init script before paint + Google Fonts).
`web/app/(dashboard)/layout.tsx` is the authenticated shell (redirects to `/login`
without a token, then renders `Sidebar` + `TopBar` + `PageTransition`).

| Route | File | Backend endpoint(s) | What it does |
|---|---|---|---|
| `/login` | `app/login/page.tsx` | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` | Login/register toggle; ambient 3D hero; pre-filled demo creds `testadmin@gmail.com` |
| `/overview` | `(dashboard)/overview` | `GET /ui/overview`, `GET /ui/matches` | KPI stat cards, recent analyses, decision-mix bars, "living" ambient background scaled by activity |
| `/analysis` | `(dashboard)/analysis` | `POST /ui/evaluate[/file]`, `POST /report/pdf`, `POST /ui/evaluate/deep-analysis` | **Flagship**: score reveal, radar, breakdown, skill constellation, tabs (Skills/Gaps/Actions/Raw), PDF export, Layer-2 deep analysis |
| `/leaderboard` | `(dashboard)/leaderboard` | `POST /ui/evaluate/file` (per file) | Multi-CV drag-drop upload, ranked cards (score-desc), Top-3 podium, distribution, CSV export |
| `/candidates` | `(dashboard)/candidates` | `GET/PUT/DELETE /ui/candidates` | Candidate CRM: edit name/email/phone/pipeline status; delete blocked when evaluations exist |
| `/jobs` | `(dashboard)/jobs` | `GET/POST/PUT/DELETE /ui/job-offers`, `…/toggle-status` | Job CRUD, `JOB-YYYY-NNN` code, status toggle, eval counts, delete-guard |
| `/history` | `(dashboard)/history` | `GET /ui/matches`, `GET /ui/matches/{id}` | Joined match table, client-side filters, raw JSON detail |
| `/insights` | `(dashboard)/insights` | `POST /ui/compare` | Side-by-side comparison of all 4 methods (no persistence) |
| `/quality` | `(dashboard)/quality` | `GET /ui/quality`, `…/figures`, `…/figures/{name}` | Offline benchmark table + provenance banner + figures + CI/subgroup/error tabs |
| `/settings` | `(dashboard)/settings` | `GET /ui/system` + client threshold state | Threshold sliders + live band preview, model cards, system status, About |

### 4.3 Design system ("Precision Intelligence")

**Token architecture** (`web/app/globals.css` + `web/tailwind.config.ts`): tokens
are CSS variables holding **space-separated RGB channels** so Tailwind's
`/<alpha-value>` opacity modifiers keep working (e.g. `bg-surface/60`). Dark is the
default (bare `:root`); light is a hand-tuned, first-class theme under
`:root[data-theme="light"]` (warm off-white grounds, colored shadows — not an
inverted dark). An explicit `[data-theme="dark"]` selector lets the toggle force
dark over system preference.

- **Color roles:** surfaces (`canvas`, `surface`, `surface-raised`,
  `surface-overlay`), borders (`subtle`/`line`/`strong`), text (`ink` /
  `ink-secondary` / `ink-muted` / `ink-inverse`). Brand hues are **constant across
  themes**: accent violet `#7c5cff` (50–900 ramp), secondary cyan `#22cfee`,
  tertiary magenta `#f65cc6`. Semantic: success `#2fd39a`, warning `#f5b445`,
  danger `#ec6a63` (each with theme-aware `-fg`/`-soft` variants).
- **Typography:** display = Space Grotesk, body = Inter, mono = JetBrains Mono
  (Google-Fonts-enhanced, system fallbacks). A full type scale from `display`
  (`clamp(2.75rem,5vw,4.5rem)`) down to `micro` (0.6875rem).
- **Radius:** 8 / 12 / 16 / 24 / 32 px. **Spacing:** 8px rhythm + a custom `4.5`
  (18px) step for 4.5-sized icons.
- **Elevation:** five layered shadow recipes `e1`–`e5` (ambient + direct light),
  tuned differently for dark (black shadows) and light (colored violet shadows);
  plus `glow-accent/success/warning/danger`.
- **Motion scale** (`web/lib/motion.ts`): spring physics over linear easing;
  micro-interactions 150–400 ms; the score reveal reserves ~1.2 s. Named
  transitions: `spring`, `springSoft`, `springSnappy`, `easeOutExpo`; variants
  `fadeUp`, `staggerContainer`, `pageTransition`, `overlayScale`, `verdictReveal`.
  Global `@media (prefers-reduced-motion: reduce)` kills animation everywhere, and
  every 3D/motion component also checks `usePrefersReducedMotion()`.

**Component library** (`web/components/ui/`, 20 files): `Badge`, `Button`, `Card`,
`CountUp`, `DataStates` (empty/loading), `Field` (Input/Select/Textarea/Label),
`Modal`, `NavItem`, `Pill`, `ProgressRing`, `RadarChart`, `StatCard`, `Table`,
`Toast`, `Toggle`, `Tooltip`. Layout: `Sidebar`, `TopBar`, `PageHeader`,
`PageTransition`, `CommandPalette`, `Logo`, `ThemeToggle`.

**3D / motion features actually built** (verified in source, not a wishlist):

- **Ambient neural field** (`components/three/NeuralField.tsx` +
  `AmbientBackground.tsx`): a low-poly drifting point/line field (≤160 edges) on
  R3F, used on Login (with cursor **parallax**) and the Overview hero. It degrades
  to a **static gradient-mesh** fallback under reduced-motion or when
  `navigator.hardwareConcurrency < 4`.
- **Living Overview background**: field `intensity` is scaled by real activity
  (evaluation volume + average compatibility), clamped to `[0.6, 1.2]`
  (`overview/page.tsx`).
- **Score object** (`components/score/ScoreObject.tsx` + `three/ScoreTorus.tsx`):
  a slow-rotating 3D torus whose arc geometry rebuilds each frame to fill to the
  score; falls back to the SVG `ProgressRing` on low-end/reduced-motion.
- **Score reveal** (`ScoreReveal.tsx`): torus fills 0→value while `CountUp` counts
  the numeral on the same ~1.2 s timeline; the `VerdictBadge` scale-ins with a glow
  only once the count finishes ("the verdict is in" beat).
- **Strong-Fit burst** (`StrongFitBurst.tsx`): a restrained ~0.9 s flare + ring +
  particles shown **only** on a HIRE verdict (skipped under reduced motion).
- **3D tilt / interactive skill constellation** (`skills/SkillConstellation.tsx`):
  an SVG with the role node at centre and skills orbiting — matched (green, solid
  edge), priority-gap (red, dashed), missing (amber, dashed), additional (violet,
  unconnected); nodes drift and highlight on hover; the SVG *is* the reduced-motion
  fallback.
- **Top-3 podium** on the Talent Leaderboard.
- **Command palette** (`CommandPalette.tsx`): a fuzzy page navigator with a
  shared-layout sliding highlight (`layoutId`), keyboard nav (↑/↓/Enter/Esc).
- **Depth skeleton loaders with shimmer**, **radar-sweep empty states**, and the
  **deep-analysis card** with staggered reveal.
- **Radar chart** (`components/ui/RadarChart.tsx`): hand-built SVG, theme-aware,
  plotting Candidate vs Required series.

---

## 5. AI/ML technologies — full inventory (the core of the project)

The evaluation runs in **two complementary layers**. Layer 1 is quantitative and
deterministic; Layer 2 is qualitative, optional, and strictly additive.

### 5.1 Layer 1 — statistical matching engine

#### 5.1.1 Document parsing & preprocessing (`src/parsing/parser.py`)

- **PDF extraction** uses **pdfplumber** first, with a **two-column layout
  parser**: `_extract_pdfplumber_page_text` reads words with `use_text_flow=True`,
  splits them at 55% of page width into left/right columns (only when the right
  column has ≥ max(3, 15% of words)), groups words into lines by rounding the
  `top` coordinate to 3-px bands, and orders each line left-to-right. Fallbacks:
  **PyPDF2** if pdfplumber is absent, then a raw `re.findall(rb"\(([^()]*)\)")`
  byte scrape as a last resort.
- **DOCX extraction** uses **python-docx** (paragraphs + table cells joined with
  `" | "`), falling back to a **stdlib zipfile + `xml.etree.ElementTree`** reader
  of `word/document.xml` (this fallback is the target of security finding **M-2**).
- **`_strip_artifacts`** removes NULs, de-hyphenates line breaks, converts
  bullets to `\n- `, and collapses whitespace.
- **`clean_text`** lowercases and scrubs URLs, emails, and **phone numbers**
  (`(?<!\w)(?:\+?\d[\d().\-\s]{7,}\d)`) — this regex is exactly what used to eat
  `2023-2026` date ranges (see Bug 1 in §5.5).
- **`tokenize_and_normalize`** uses spaCy lemmatisation *if a model is installed*
  (`fr_core_news_lg` → `en_core_web_lg` → small variants), otherwise a
  `_naive_lemma` suffix-stripper that protects technical tokens (`+ # . / -`) and
  a hand-built bilingual (EN+FR) stopword set (~190 words).
- **`segment_cv`** splits a CV into `summary / experience / education / skills /
  languages / certifications / projects / other` using multilingual heading
  regexes, with keyword-based fallbacks when a section heading is absent.

#### 5.1.2 Keyword relevance — `TFIDFMatcher` (`src/models/tfidf_model.py`)

- `sklearn.feature_extraction.text.TfidfVectorizer` with **`ngram_range=(1,3)`,
  `max_features=10000`, `sublinear_tf=True`, `min_df=2`** (auto-relaxed to
  `min_df=1` for < 4 documents or on a `ValueError`).
- `predict(cv, job)` = **cosine similarity** of the two TF-IDF vectors, clipped to
  `[0,1]`. It **requires the vectorizer to be fitted** (`_ensure_fitted_for_inputs`
  raises otherwise) — the production checkpoint carries the fitted vectorizer.
- Operates on the **raw text passed in** (no internal `clean_text`), relying on
  scikit-learn's default tokenisation/stopword behaviour.

#### 5.1.3 Semantic relevance — `EmbeddingMatcher` (`src/models/embedding_model.py`)

- **Dual SentenceTransformer backends**: English (`EMBEDDING_MODEL_EN`, default
  `all-mpnet-base-v2`) + multilingual (`paraphrase-multilingual-mpnet-base-v2`).
  Loaded with `model_kwargs={"low_cpu_mem_usage": False}` to disable the
  transformers ≥4.47 threaded materialiser that crashes on Python 3.13 + Windows.
- **HashingVectorizer fallback (`_LocalEmbeddingBackend`)**: used when
  `sentence-transformers` is not importable *or* a model fails to load. It stacks
  word n-grams (1–2, 2048 features) and char n-grams (3–5, 2048 features) →
  **4096-dim L2-normalised sparse** vector. It logs a one-time warning. This is a
  **token-overlap approximation, not true semantics** — it measures sub-string
  overlap, degrading "semantic relevance" toward an advanced keyword matcher. The
  fallback triggers on memory-constrained environments (e.g. the Windows box's
  paging-file limit) — documented in `web/REBUILD.md` and `PROJECT_REPORT.md`.
- **Scoring** (`predict`): `base = 0.5·en_sim + 0.5·ml_sim`; `section =
  section_aware_similarity(segment_cv(cv), job)` with section weights **experience
  0.40 / skills 0.30 / summary 0.15 / education 0.10 / languages 0.05**
  (renormalised over present sections); final = **`0.7·base + 0.3·section`**,
  clipped to `[0,1]`.
- **Caching**: per-text encodings cached in a dict with **FIFO eviction** at 8192
  entries; keyed by an MD5 of the text (security finding **L-5**, non-sensitive).
  `batch_predict` pre-collects unique texts and batch-encodes each backend once.

#### 5.1.4 Skills assessment — `SkillMatcher` + `SkillExtractor`

**Extraction** (`src/nlp/skill_extractor.py`) combines three signals:

1. **Dictionary lookup** against `data/datasets/skills_dictionary.json` using
   pre-compiled boundary-guarded regexes, after alias expansion (built-in variants
   like `ml→machine learning`, `k8s→kubernetes`, plus the dictionary's 67
   aliases).
2. **Rule-based NER** via spaCy's `EntityRuler` (only if spaCy is installed) —
   labels skills as LANGUAGE / FRAMEWORK / TOOL / SKILL / CERTIFICATION by category.
3. **1-/2-/3-gram sliding windows** checked against the dictionary whitelist.

Signals are merged with a per-skill **confidence score** (`0.45 + layer_boost +
mention_boost`, capped 0.99). The payload also carries `years_experience`,
`experience_detected` (honest not-detected flag), `education_level`, `domain`, and
`confidence_scores`.

- **Experience detection** (`_detect_years_experience`, run on **raw** text):
  explicit "N years/ans" phrases **and** date ranges with separators `- – —`,
  `to/until/au/à/jusqu'à`, open-ends `present/current/now/actuel/en cours`
  resolving to today, EN+FR month names for month precision; durations **summed
  across entries**; returns `None` (not 0) when nothing parses.
- **Domain detection**: scores 17 `domain_keywords` groups; returns the best or
  `generalist`.

**Scoring** (`src/models/skill_matcher.py::predict_detailed`):

- `hard_score` = `|cv_hard ∩ job_hard| / |job_hard|`; `soft_score` likewise for
  soft skills.
- `base = (0.70·hard + 0.30·soft)` with weights **dynamically redistributed** if a
  category is absent in the job (e.g. no soft skills listed → hard gets full
  weight).
- **Bonuses:** `+0.05` domain match; `+0.03` per relevant certification, capped
  `+0.10`.
- **Critical penalty:** `0.20 · (|critical_missing| / |critical_skills|)` — up to
  **−0.20**. (Note: `TECHNICAL_DOCUMENTATION.md` says "0.10 penalty"; the code is
  0.20 — the code is authoritative.)
- **Critical skills** are those appearing in a JD sentence containing a trigger
  (`required / must / mandatory / obligatoire / essentiel / indispensable / need`).
- Final = `clip(base + domain_bonus + cert_bonus − critical_penalty, 0, 1)`.
- Categorises skills into **matched / missing / extra / critical-missing**, and
  emits coverage text `"{matched_hard}/{job_hard or 1} required skills"`.

#### 5.1.5 Hybrid fusion — `HybridMatcher` (`src/fusion/hybrid_scorer.py`)

- **Fusion:** `final = w_tfidf·tfidf + w_embedding·embedding + w_skill·skill`,
  clipped `[0,1]`. **Documented default weights (`DOCUMENTED_DEFAULT_WEIGHTS`) =
  `tfidf 0.2 / embedding 0.4 / skill 0.4`.** Verified: the shipped checkpoint
  `models/checkpoints/hybrid.pkl` carries exactly `{'tfidf':0.2,'embedding':0.4,
  'skill':0.4}` with `optimal_threshold = 0.2636`.
- `predict()` returns `final_score`, `percentage`, a `label` (vs
  `optimal_threshold`), a **sigmoid-based `confidence`** string (this is a *score*
  confidence and explicitly **not** a calibrated probability), `component_scores`,
  `weights_used`, and full `skill_details`.
- **Weight optimisation** (`optimize_weights`) exists — a grid search over
  embedding/skill weights maximising validation AUC — but the production export
  path deliberately **does not** use it (see §5.4, Bug 4). `calibrate_threshold`
  selects the operating point by best-F1 on validation, with ties broken toward
  0.60. `cross_validate` provides k-fold reporting.

#### 5.1.6 Decision engine (`src/decisioning/decision_engine.py`) — single source of truth

- **Classification:** `pct ≥ strong → HIRE ("Strong Fit")`; `potential ≤ pct <
  strong → CONSIDER ("Potential Fit")`; else `REJECT ("Low Fit")`. Defaults
  **strong = 75.0, potential = 55.0**.
- **`DecisionConfig`** is a frozen, strictly-validated dataclass: rejects
  non-numbers, `bool`, `NaN`, out-of-range, and `potential ≥ strong`.
- **Decision confidence** (uncalibrated): `nearest_distance_to_a_threshold / 20.0`,
  clamped `[0,1]`; bands high ≥0.66 / medium ≥0.33 / low. Explicitly **not** a
  probability of hire.
- `to_percentage` accepts a 0–1 fraction or a 0–100 percentage and normalises.
- This engine is the ONE place mapping score→decision. It replaced the earlier
  "four disagreeing decision paths" bug (`FUNCTIONAL_AUDIT.md` B1–B3). Both the
  persisted `MatchResult.decision` and the explanation's `hiring_recommendation`
  come from the **same** engine+config, so they cannot disagree.

#### 5.1.7 Explainability (`src/explainability/explainer.py`)

- `MatchingExplainer.explain()` produces `global_score`, `verdict`,
  `hiring_recommendation`, `experience_fit`, `semantic_analysis`,
  `skill_analysis`, `gap_analysis`, and **`radar_data`** — deriving the decision
  via the `DecisionEngine`.
- **5-axis radar** (labels: Technical, Semantic, Experience, Soft Skills, Domain):
  - **Technical** = `skill_score·100`; **Semantic** = `embedding_score·100`.
  - **Experience** = `min(100, candidate_years / required_years · 100)` (with an
    `experience_detected` flag so a *parse failure* renders as N/A, not a real 0).
  - **Soft Skills** = `min(100, 20·|cv_soft_skills|)`.
  - **Domain** = 90 if candidate/job domains match, else 50.
  - **Required (per-job) vector** (Bug 3 fix): each axis is tagged in
    `job_requirements_source` as `"job"` (derived) or `"benchmark"`. Domain is
    always job-derived; Soft is job-derived when the JD lists soft skills (else
    benchmark 65); Experience = 100 when the JD states required years (else
    benchmark 70); **Technical (85) and Semantic (80) are explicit benchmarks**
    because the `JobOffer` model has no structured field to derive them from.
- **`RecommendationEngine.generate()`** maps gaps to a `RESOURCE_MAP` of ~25
  learning URLs (default `roadmap.sh`), estimates learning weeks
  (`max(2, 2·critical + max(1, minor))`), and a `match_potential`
  (`min(98, 70 + 6·critical + 2·minor + 3·strengths)`).

> **Dead-code note (worth flagging in the thesis):** `MatchingExplainer._verdict`
> and `_hiring_recommendation` (the old 80/60/45 band logic) are **no longer
> called** — `explain()` routes entirely through `DecisionEngine`. They remain in
> the file as legacy and can mislead a reader; the PDF generator's
> `_build_decision_section` also has a similar dormant fallback branch that only
> runs if `hiring_recommendation` is absent (it never is).

### 5.2 Model provenance & the production checkpoint

- **No embedding fine-tuning.** The MPNet/MiniLM/multilingual weights are
  pretrained, downloaded from HuggingFace. Only the **TF-IDF vocabulary** and the
  **fusion weights + operating threshold** are trained/serialised locally.
- **`models/checkpoints/hybrid.pkl`** is produced by
  `scripts/export_production_model.py`: it applies the same pair-group-disjoint
  split as the benchmark, uses the **documented fixed weights** (no weight search),
  calibrates the threshold on validation only, refits TF-IDF on **train+validation**
  (never test), and strips the (stateless, re-instantiated) embedding/skill models
  before pickling. `model_loader.load_production_models()` loads it, **fails loudly**
  if TF-IDF is unfitted, and re-injects fresh Embedding/Skill matchers.

### 5.3 Layer 2 — LLM qualitative reasoning (`src/ai/`)

- **Why an LLM reasoning layer instead of a trained classifier?** There is **no
  real labelled hiring-outcome dataset**; training on small synthetic data invites
  exactly the leakage/overfitting seen in Layer 1 (Bug 4). A pretrained LLM brings
  broad world knowledge zero-shot, with no parameter fitting to an untrusted
  dataset (`LLM_LAYER.md §1`).
- **Runtime:** a **local Ollama** server (`http://localhost:11434`), chat API in
  **JSON mode** (`format: "json"`), options `temperature 0.2, num_ctx 8192,
  num_predict 2048`.
- **Model:** default **`qwen2.5:1.5b`** (quantized, ~986 MB download, ~1.4 GB
  resident). Chosen as the smallest model that produced a grounded, first-attempt
  schema-valid analysis on the 8 GB / CPU-only verification machine (0.5B was too
  shallow; ≥3B risked the RAM budget). Overridable via `OLLAMA_MODEL` (e.g.
  `llama3.1:8b` on bigger hardware) with no code change.
- **Prompt design** (`src/ai/prompts/deep_analysis_prompt.py`): (1) **grounding** —
  the user prompt injects Layer 1's scores/skills/experience and asks the model to
  *interpret*, not re-score; (2) **no competing number** — the system prompt
  forbids emitting its own percentage or overturning the decision; (3) **fairness**
  — an explicit instruction to ignore/never reference protected characteristics
  (age, gender, ethnicity, nationality, religion, marital status, disability,
  orientation, photos); (4) **strict JSON** with a spelled-out `RESPONSE_SCHEMA`;
  (5) CV/JD truncated to 6 k / 4 k chars.
- **Output schema** (`ai_deep_analysis.analysis`): `career_trajectory
  {summary, seniority_signal, progression}`, `red_flags[{issue, severity,
  evidence}]`, `recommendations[{recommendation, rationale}]`, `fit_justification`,
  `interview_questions[{question, targets}]`.
- **Service** (`src/ai/llm_reasoning.py`): pure, never raises to the caller —
  returns an **envelope** `{status, model, generated_at, latency_ms, analysis,
  error}` with `status ∈ {ok, disabled, unavailable, error, inconsistent}`. It
  probes availability (`/api/tags`), parses tolerantly (strips fences, extracts
  the first balanced `{...}`), **validates** required keys/types, and **retries
  once** with a repair hint on malformed output.
- **Consistency guard (`_contradictory_claims`)** — added after a hallucination
  bug (commit `803eb07`): for **REJECT / low-coverage (< 0.5)** cases it screens
  the narrative against a regex denylist of positive phrases ("strong alignment",
  "perfect match", "no red flags", "ideal candidate", …), ignoring explicit
  negations ("not a strong fit"). On a contradiction it retries once with a
  stronger hint, and if it still contradicts, returns `status="inconsistent"` and
  a graceful "unavailable" narrative. **Limitation (finding M-3):** it is a
  bypassable denylist and does **not** run for HIRE/CONSIDER cases.
- **Endpoints** (additive, on `/ui`): `POST /ui/evaluate/deep-analysis
  {match_id}` reconstructs Layer 1's results from the persisted `MatchResult`,
  calls Layer 2, persists a successful envelope into `llm_analysis_json`, and
  returns it; `GET /ui/deep-analysis/health` reports Ollama reachability. It is
  fired by the frontend **after** the score renders, so LLM latency never blocks
  the verdict.
- **Genuine verified run** (`LLM_LAYER.md §7`, `scripts/verify_deep_analysis.py`):
  the Alex Martin / Full-Stack case, local `qwen2.5:1.5b`, completed in
  **51,672.3 ms**, `status: ok` on the first attempt, no retry — Layer 1 result
  75.9% / HIRE / 11-of-11 skills. The full payload is transcribed in `LLM_LAYER.md`.

### 5.4 Benchmark / evaluation methodology (`src/evaluation/evaluator.py`)

- **Dataset:** `data/datasets/cv_job_dataset.csv` — **12,000 rows, 0 duplicate
  (cv,job) pairs**, label distribution **8,414 positive / 3,586 negative**, 19
  domains, 4 seniority bands (junior/mid/senior/lead), plus `score_raw`, per-side
  hard/soft skills, `match_reason`, `difficulty`. Synthetic, EN+FR mixed, generated
  by `data/datasets/generate_dataset.py` (seed 42) from 19 `DOMAIN_BLUEPRINTS` with
  injected realism (typos, obsolete skills, contradictory offers, abbreviations,
  hybrid profiles, cert-heavy, cross-lingual).
- **Split:** `stratified_split` groups rows by a **normalized (cv+job) pair hash**,
  asserts groups are **disjoint** across train/validation/test, and stratifies by
  `label × domain`. Sizes **8,400 / 1,800 / 1,800** (verified in
  `evaluation_results.json`).
- **Calibration:** fixed documented fusion weights; **one operating threshold per
  method calibrated on validation only** (best-F1, ties → 0.60); metrics reported
  once on the untouched test split. A regression warning fires if AUC ≥ 0.80 with
  F1 ≤ 0.05 (the old bug's signature).
- **The bug history (Bug 4 + benchmark integrity):** the *old* production
  checkpoint had been "optimised" to **tfidf 0.9 / embedding 0.0 / skill 0.1** with
  a degenerate `optimal_threshold = 0.04` (an artifact of grid-searching a
  synthetic validation split). With embedding weighted 0.0, an "echo" CV
  (mirroring JD wording) scored 99.2% vs a semantically-equivalent paraphrase at
  73.6% — a **25.6-point keyword-gaming swing**. The fix (commit `38e50e8`)
  re-exported the checkpoint at the documented **0.2/0.4/0.4** with a
  validation-calibrated **0.2636** threshold; the post-fix echo/paraphrase gap
  fell to **9.6 points**. The old offline harness also applied a hard-coded 0.60
  cutoff to every component, producing the high-AUC/near-zero-F1 pathology.

**Final honest metrics (current `evaluation/results/evaluation_results.json`, test
n = 1,800):**

| Method | Threshold | Accuracy | Precision | Recall | F1 | AUC-ROC | ms/pair |
|---|---|---|---|---|---|---|---|
| TF-IDF (Keyword) | 0.0395 | 0.928 | 0.928 | 0.973 | **0.950** | 0.979 | 0.24 |
| Semantic (Embedding) | 0.5353 | 0.777 | 0.809 | 0.894 | 0.849 | 0.811 | **921.6** |
| Skills | 0.0023 | 0.894 | 0.892 | 0.967 | 0.928 | 0.947 | 53.1 |
| **Hybrid (Overall)** | **0.2636** | 0.908 | 0.939 | 0.930 | 0.934 | 0.964 | 55.9 |

Additional analysis in the file: bootstrap 95% CIs per metric; **McNemar** tests
(hybrid vs embedding p ≈ 2e-37 — significant; hybrid vs skill p ≈ 0.074 — not
significant); **subgroup AUC** by seniority (0.947–0.974) and by all 19 domains;
error analysis (76 FP / 89 FN, dominant domains). The provenance is surfaced
honestly in the Quality Center as an offline, non-live benchmark.

> Note the very high TF-IDF/skills F1 on this *synthetic* dataset — the CV and JD
> texts are generated from the same skill vocabulary, so lexical overlap is an
> unusually strong signal here. This is a property of the synthetic data, not
> evidence that keyword matching would dominate on real CVs; it is exactly the
> reason the production weighting keeps embedding + skills at 0.4 each rather than
> chasing TF-IDF's benchmark F1. This caveat belongs in the thesis.

### 5.5 Every real matching-engine bug found & fixed (`BUGFIXES.md`, verified)

- **Bug 1 — experience parsing.** `_detect_years_experience` had no date-range
  parser, and `clean_text`'s phone scrubber deleted compact `YYYY-YYYY` ranges.
  Result: date-range experience → 0 years → Experience radar 0%. **Fix:** full
  raw-text range parser (EN+FR, months, open-ends, summed) + an honest
  `experience_detected` flag distinguishing "not detected" from "confirmed zero".
- **Bug 2 — HTML/CSS invisible.** `skills_dictionary.json` lacked `html`/`css`,
  so required web skills silently dropped from the coverage denominator (11→9).
  **Fix:** added `html`, `css`, `responsive design` + aliases (`html5→html`,
  `css3→css`, `scss→sass`); `metadata.hard_skill_total` bumped 1039→**1042**.
- **Bug 3 — hardcoded radar "Required".** The required vector was a constant
  `[85,80,70,65,80]`. **Fix:** per-job derivation where the model allows, with a
  `job_requirements_source` label ("job" vs "benchmark") for honesty.
- **Bug 4 — keyword-gaming score inflation.** See §5.4 (resolved by re-exporting
  the checkpoint at documented weights). Historical `MatchResult` rows created
  before 2026-09-09 are a **documented, intentionally-retained score-scale
  discontinuity**.

---

## 6. DevOps & engineering practices

### 6.1 Version control

- Single Git repo, `main` branch, plus a feature branch `fix/ai-engine-bugs`.
  Observed **Conventional-Commits** style throughout (`feat`, `fix`, `test`,
  `docs`, `chore` with scopes: `feat(3d)`, `fix(radar)`, `fix(llm)`,
  `docs(evaluation)`, etc.). Recent history shows an issue-driven cadence: parity
  rebuild → motion/3D polish → engine bug fixes → LLM layer → evaluation
  calibration → LLM fail-closed → rename. No tags. Attribution/PR conventions were
  not observable beyond the commit log.

### 6.2 Testing

- **Framework:** pytest (`pytest.ini`: `testpaths = tests`, cache disabled,
  `--basetemp=tests_tmp/pytest`, and `norecursedirs = frontend web node_modules
  .venv` — the deprecated Streamlit UI is excluded from routine collection).
- **Test files & counts** (14 files, **96 `test_` functions**; 113 test items
  collected at run time):

  | File | `test_` fns | Covers |
  |---|---|---|
  | `test_parsing.py` | 5 | PDF/DOCX parsing, clean_text |
  | `test_models.py` | 3 | TF-IDF / cosine behaviour |
  | `test_skill_extractor.py` | 10 | skill categorisation, experience parser (Bug 1/2 regressions) |
  | `test_fusion.py` | 4 | hybrid weighting/fusion |
  | `test_decision_engine.py` | 12 | boundaries, invalid configs, confidence |
  | `test_matching_consistency.py` | 5 | explainer==engine, dedup, stable anon IDs, metadata |
  | `test_llm_reasoning.py` | 19 | Layer 2 with Ollama **mocked** (parsing, validation, consistency guard) |
  | `test_evaluation_integrity.py` | 3 | pair-group disjointness, calibration |
  | `test_pdf_generator.py` | 8 | PDF byte structure |
  | `test_api.py` / `test_api_extended.py` | 1 / 11 | FastAPI routing/responses |
  | `test_auth.py` | 6 | register/login/JWT |
  | `test_data_architecture.py` | 3 | schema/data rules |
  | `test_production_model.py` | 6 | checkpoint loading/validation |

- **Mocking:** `tests/conftest.py` autouses a session-scoped mock of
  `SentenceTransformer` (deterministic 384-dim random vectors) to avoid real model
  loading — which crashes Python 3.13 + PyTorch inside anyio's thread pool.
- **Actual result of running `pytest -q` during this audit:**
  **106 passed, 6 failed, 1 skipped (81 warnings), ~45 s.** The 6 failures are all
  in `test_api_extended.py` (legacy `/match`, `/rank`, `/report/pdf`): they now
  return **404** because those endpoints gained the recruiter-scoped IDOR guard
  (`_assert_owned`, security fix H-1) but the test fixtures build job rows that do
  not satisfy ownership in the test DB session. These are **pre-existing,
  documented, unrelated test/fixture drift** (noted in `FUNCTIONAL_AUDIT.md
  §11`), not regressions in shipped behaviour. Honest thesis statement: *~94% of
  the suite passes; the failing 6 are stale API tests not updated after the
  security scoping change.*

### 6.3 Dependency management & the environment-corruption incident

- **Python:** `pip` + `requirements.txt` (pinned `scikit-learn==1.8.0`,
  `bcrypt==3.2.2`; the file has the corrupted trailing `bcrypt` line noted in
  §3.2). **Node:** npm + `web/package-lock.json` (committed).
- **Environment-corruption incident:** `SECURITY_AUDIT.md`/history reference an
  antivirus interfering with npm extraction during setup; it was worked around and
  the build re-verified green. This is a genuine engineering obstacle worth a
  one-line mention as a "challenge overcome," though the repo itself carries no
  artifact of the incident beyond the resolved lockfile.

### 6.4 Build / verification process

- Backend "done" = importable + `pytest` green + (for engine changes) targeted
  regression tests. Frontend "done" = `npm run build` green (`web/REBUILD.md`
  records the Next.js 14.2.18→14.2.35 bump was build-re-verified). The Next.js
  rebuild was additionally **verified live** end-to-end against the real backend
  across all 10 pages (`web/REBUILD.md`).

### 6.5 Repository hygiene (honest observation)

The project root carries substantial **development scatter** that a thesis
appendix should acknowledge but that is not part of the shipped system:
`debug.log`, `debug2.txt`, `debug3.txt`, `out.txt`, `out2.txt`, `debug_ui.py`,
`search_js.py`, `fix_tests.py`, `fix_widths.py`, `scratch_e2e_test*.py`,
`scratch_eval*.py`, `test_workflow.py`/`test_workflow.db`, `test_db_endpoints.py`,
`audit_script.py`, and several PDF-report generators (`build_reports*.py`,
`generate_*.py`) used to produce evidence documents. `data/backups/` holds 22
timestamped `.bak` SQLite snapshots. **Alembic** is configured (`alembic.ini`,
`alembic/env.py`) but the only migration (`75dbc3bf48c2`) merely adds
`users.full_name`; real schema evolution is instead handled by the additive
`db_maintenance.ensure_schema` at API startup.

---

## 7. Cybersecurity

Full findings live in `SECURITY_AUDIT.md` (dated 2026-09-13; a static
code/config review — npm audit, pip-audit, bandit, secret grep + manual review of
auth, access control, upload, injection, XSS, CORS, rate limiting, the LLM layer,
and PDF generation). Summary of what was **checked, found, and fixed vs. accepted**:

**Fixed in the audit pass:**

- **C-1 (Critical) — hardcoded default JWT secret.** The secret used to fall back
  to the well-known FastAPI-tutorial literal → anyone could forge a token → full
  auth bypass. **Fixed:** `config.py` now falls back to a random per-process
  `secrets.token_hex(32)` with a startup warning; `JWT_SECRET_KEY` must be set for
  stable sessions.
- **H-1 (High) — IDOR on legacy match endpoints.** `/match`, `/match/file`,
  `/rank` were authenticated but not recruiter-scoped (cross-tenant job read /
  match write). **Fixed:** added `_assert_owned()` + recruiter filters; also fixed
  a latent `NameError` (`processing_time`) on the persist path. (This fix is why 6
  legacy API tests now 404 — §6.2.)
- **H-2 (High) — vulnerable Next.js.** Bumped `14.2.18 → 14.2.35` (latest 14.x
  patch); the advisory DB only considers Next 16 fully clean, so a Next-16
  migration is a documented follow-up. Risk accepted as low for a localhost thesis
  deployment.

**Documented follow-ups / accepted limitations:**

- **M-1** — file upload has no size cap (`await cv_file.read()` loads whole file)
  and extension-only type checking (no magic-byte validation). No path-traversal
  (uploads use `tempfile.NamedTemporaryFile`).
- **M-2** — the DOCX **zipfile fallback** parses `document.xml` with stdlib
  `xml.etree` (billion-laughs XXE/entity-expansion DoS surface). Recommended fix:
  `defusedxml`.
- **M-3** — **LLM prompt injection**: CV/JD text is user-controlled and embedded
  in the prompt. Mitigations: the statistical engine (not the LLM) owns the
  score/decision, so injection can only skew advisory narrative; the consistency
  guard fails closed for REJECT/low-coverage. Residual: the guard is a bypassable
  denylist and doesn't run for HIRE/CONSIDER. Recommendation: label the panel as
  advisory/untrusted.
- **L-1** reportlab `Paragraph` markup not escaped for `candidate_name`/`job_title`
  (no RCE; cosmetic). **L-2** `pickle.load` of the project's own trusted
  checkpoint. **L-3** weak auth policy (no password complexity, `email` is a free
  string with no format validation, login user-enumeration timing side-channel).
  **L-4** rate limiting is in-memory/per-IP with no per-account lockout. **L-5**
  MD5 used only for cache keys (not security).

**Confirmed OK:** secrets gitignored (`.env`, `*.db`; only `.env.example`
tracked); **bcrypt** hashing via passlib with a 71-byte password cap; JWT `exp`
enforced (HS256, `python-jose`); every data endpoint depends on
`get_current_user`; all `/ui/*` list/CRUD/evaluate endpoints filter by
`recruiter_id`; CORS is an explicit localhost allow-list (not `*`) with
`allow_credentials=True`; all DB access is via the ORM (no raw SQL string
interpolation in queries — the only raw SQL is the parameterised/id-list
maintenance migration in `db_maintenance.py`); the only
`dangerouslySetInnerHTML` is the static theme-init script; the figures route has
an explicit path-traversal guard.

**Data-privacy design decision:** recruiter-scoped data isolation
(`recruiter_id == current_user.id` everywhere) is a deliberate change from the
legacy Streamlit app's **global visibility** (`KNOWN_DEVIATIONS.md §2`). GDPR-style
affordances exist: `DELETE /candidates/{id}` (hard delete + cascade) and
`POST /candidates/{id}/anonymize` (strip PII, keep analytics).

---

## 8. Cloud hosting / deployment

**Honest, code-grounded status.** The repository does **not** contain any Azure
VM, Vercel, or Next.js-container configuration. What exists on disk:

- `docker-compose.yml`: `db` (Postgres 16, healthcheck), `api` (uvicorn :8000,
  `env_file: .env`, depends on healthy db), `frontend` (**Streamlit** :8501). Named
  volume `postgres_data`. Postgres creds come from `.env` (`.env.example` uses `jobtest`).
- `Dockerfile.api` and `Dockerfile.frontend`: identical `python:3.11-slim` images
  that install CPU-only Torch (`--index-url https://download.pytorch.org/whl/cpu`)
  + `requirements.txt`; they only `EXPOSE` 8000/8501 and rely on compose for the
  run command. **Neither builds the Next.js app.**
- `.dockerignore` excludes `.venv`, caches, `tests_tmp`, evaluation outputs.

**The intended production topology** (Azure VM hosting backend + Ollama + DB,
Vercel hosting the Next.js frontend) is described in the project brief and is a
reasonable plan — Azure Student/Free-Trial gives enough RAM for local `qwen2.5:1.5b`
inference where free tiers (Oracle Cloud, HF Spaces, GitHub Actions) do not, and
Vercel natively hosts Next.js on a generous free tier with a global CDN — **but it
is not represented by any file in the repo and the shipped `docker-compose.yml`
actually wires the legacy Streamlit frontend, not Next.js.** The only concrete
hardware profile evidenced anywhere is the LLM verification machine in
`LLM_LAYER.md` (7.75 GB RAM / 4 vCPU / ~1.96 GB free / CPU-only). The platform is
explicitly intended for **periodic demo/defense use, not permanent 24/7 hosting**,
for cost/credit reasons. **Recommendation for the thesis:** present §8 as
"intended deployment" and either add the missing Vercel/Next-container config or
state clearly that deployment was done manually outside version control.

---

## 9. Data model (`src/models_db.py`)

SQLAlchemy 2.0 ORM on **SQLite by default** (`data/jobtest.db`; Postgres under
docker). Foreign keys enforced on SQLite.

- **User** — `id, email (unique, indexed), hashed_password, full_name, role
  (default "recruiter"), created_at`. 1→N `JobOffer`, 1→N `Candidate`.
- **Candidate** — `id, full_name, email (unique, indexed, nullable), phone,
  recruiter_id→users, status (NEW|UNDER_REVIEW|SHORTLISTED|INTERVIEW|REJECTED|
  HIRED, default NEW), is_anonymous (0/1), created_at, updated_at`. 1→N `CV`
  (cascade delete), 1→N `MatchResult` (cascade delete).
- **CV** — `id, candidate_id→candidates (required), filename, content_text
  (required), extracted_skills_raw, uploaded_at`. N↔N `Skill` via `cv_skills`.
- **JobOffer** — `id, job_code (unique, indexed, nullable), title, description,
  required_skills_raw, recruiter_id→users, status (OPEN|ON_HOLD|CLOSED, default
  OPEN), created_at, updated_at`. 1→N `MatchResult` (cascade). N↔N `Skill` via
  `job_skills`.
- **MatchResult** — the canonical evaluation record: `id, candidate_id, cv_id,
  job_offer_id`; scores `final_score, score_hybrid, score_semantic, score_keyword,
  score_skill`; `confidence` (legacy level string), `decision`
  (HIRE|CONSIDER|REJECT); **reproducibility metadata** `decision_confidence,
  strong_fit_threshold, potential_fit_threshold, model_version, evaluation_method,
  weights_json`; `model_used, explanation_json`, the additive
  **`llm_analysis_json`** (Layer-2 envelope), and `created_at`.
- **Skill** — `id, name (unique), category`. Association tables `cv_skills`,
  `job_skills` exist but are lightly used by the current write paths (the matching
  service persists a `CV` row and the `MatchResult`, not normalized skill links).

**Persisted vs. computed:** Candidate/CV/JobOffer/MatchResult and the full
explanation+recommendations JSON are persisted per evaluation. **AI Insights**
(model comparison) and the **AI Quality Center** benchmark are computed on the fly
/ file-backed and never written to the DB. The Layer-2 analysis is persisted only
on `status == "ok"`.

> **Latent schema quirk (worth flagging):** `Candidate.email` carries a **global**
> `unique=True` constraint, but `_resolve_candidate` de-duplicates by
> `(recruiter_id, email)`. Two different recruiters therefore cannot both store a
> candidate with the same email — the DB constraint is stricter than the
> application's per-recruiter intent. Not a security issue, but a real modelling
> inconsistency for a multi-recruiter deployment.

---

## 10. Backend API surface

All data endpoints require `Depends(get_current_user)`. Base prefix `/api/v1`.

**System:** `GET /` → redirect to docs; `GET /health`; `GET /health/detailed`
(probes each model); `GET /metrics` (usage counters).

**Auth (`/api/v1/auth`):** `POST /register` (71-byte password cap), `POST /login`
(OAuth2 password form → JWT bearer), `GET /me`.

**Core matching / DB (in `main.py`):**
- `POST /match` — text match; `job_offer_id` required; IDOR-guarded; persists a
  `MatchResult` when `candidate_id`+`job_offer_id` given.
- `POST /match/file` — PDF/DOCX upload variant (temp file, deleted in `finally`).
- `POST /rank` — rank ≤30 candidates against one owned job (score-desc).
- `POST /report/pdf` — reportlab PDF from a precomputed payload.
- `GET /models/compare` — all 4 models on one CV/JD pair.
- `POST/GET /candidates`, `POST/GET /job-offers`, `GET /matches`,
  `GET /matches/{id}` — recruiter-scoped CRUD/read.
- `DELETE /candidates/{id}`, `POST /candidates/{id}/anonymize` — GDPR.

**UI parity router (`/api/v1/ui`)** — what the Next.js app actually uses:
`GET /overview`; job offers `GET/POST /job-offers`, `PUT /job-offers/{id}`,
`POST /job-offers/{id}/toggle-status`, `DELETE /job-offers/{id}` (409 if
evaluations exist); candidates `GET /candidates`, `PUT /candidates/{id}`,
`DELETE /candidates/{id}` (409 if applications exist); history `GET /matches`,
`GET /matches/{id}`; evaluation `POST /evaluate`, `POST /evaluate/file` (both route
through `evaluate_and_persist` with the session's thresholds); Layer 2
`POST /evaluate/deep-analysis`, `GET /deep-analysis/health`; `POST /compare`
(no persist); `GET /quality`, `GET /quality/figures`, `GET /quality/figures/{name}`
(traversal-guarded); `GET /system`.

CORS: explicit localhost allow-list; methods GET/POST/PUT/DELETE/PATCH/OPTIONS.

---

## 11. Conception & design methodology

### 11.1 Functional requirements as implemented (recruiter capabilities)

A logged-in recruiter can: create/edit/close/delete job offers (auto-coded
`JOB-YYYY-NNN`, delete-guarded); manage candidates (edit identity + pipeline
status, delete-guarded, anonymize/delete for GDPR); evaluate a single candidate
against a job (paste or upload, choose model, name/email optional) and read a full
explainable result; export a PDF; bulk-rank many CVs against one job; browse
candidate/job/analysis history scoped to themselves; compare the four scoring
methods live; review the offline benchmark with honest provenance; and configure
the active decision thresholds (session-scoped). These map cleanly onto UML
use-cases for the "Analyse et conception" chapter.

### 11.2 Design evolution (the actual, iterative, issue-driven methodology)

Streamlit prototype → additive `/ui` parity router → **full Next.js rebuild** with
verified functional parity → design/motion/3D polish pass → **AI-engine bug fixes**
(experience parsing, skill dictionary, radar honesty) → **benchmark integrity**
overhaul (calibrated thresholds, pair-disjoint splits, documented weights) →
**Layer-2 LLM reasoning** (additive, then fail-closed consistency guard) →
**security + deployment hardening** → **rename to JobTest**. Each step is traceable
in git and in a dedicated `*_AUDIT.md`/`*.md` companion document.

### 11.3 Known, deliberate deviations from the Streamlit app (`KNOWN_DEVIATIONS.md`)

1. **AI Insights is non-persisting** — the old page called the persisting path
   with no `job_offer_id` and crashed on every use; the new page uses
   `run_evaluation` (a comparison must never write match records).
2. **Recruiter-scoped data** — every surface filters by `recruiter_id`, replacing
   the old global visibility.
3. **AI Insights / Quality Center non-persistence** and the **hybrid-weight
   correction** (score-scale discontinuity for pre-2026-09-09 rows) are documented,
   intentional decisions.

---

## 12. Full platform workflow (demo script, step-by-step)

1. **Register / login** (`/login`) → JWT stored; redirect to `/overview`.
2. **Overview** → KPI cards (candidates, avg compatibility, HIRE rate, open jobs,
   total reports), recent analyses, decision-mix bars; ambient field breathes with
   activity.
3. **Create a Job Offer** (`/jobs`) → title/description/required skills → assigned
   `JOB-YYYY-NNN`, status OPEN.
4. **Candidate Analysis** (`/analysis`) → pick job, choose method (default
   hybrid), optional name/email, paste text or upload PDF/DOCX → **Run
   Evaluation**.
5. **Layer 1** parses → extracts skills → TF-IDF/semantic/skill sub-scores → hybrid
   fuse → DecisionEngine verdict → persisted as a `MatchResult`.
6. **Result view** → animated score ring/torus + count-up, verdict badge (HIRE
   triggers the burst), competency radar (Candidate vs Required), score breakdown,
   experience fit, and tabs: Skills Match (constellation/list), Strengths & Gaps,
   Recommended Actions (learning links, ramp-up estimate, keywords, CV tips), Raw
   Data.
7. **Layer 2 (AI Deep Analysis)** fires after the score renders → recruiter
   summary, career trajectory, red flags, personalized recommendations, tailored
   interview questions — or a graceful "unavailable" state if Ollama is down.
8. **Export PDF** → 7-section report (profile, score+donut+bars, competency radar
   + gap table, skills, strengths/gaps, recommendations, decision support with
   interview focus areas).
9. **Talent Leaderboard** (`/leaderboard`) → drag-drop many CVs → each evaluated +
   persisted → ranked cards + Top-3 podium + distribution + CSV export.
10. **History** (`/history`) → all persisted matches, filterable; drill into raw
    JSON. **Candidates/Jobs** → manage records.
11. **AI Insights** (`/insights`) → all four methods side-by-side on one CV/JD (no
    persistence).
12. **AI Quality Center** (`/quality`) → offline benchmark table + provenance
    banner + figures + CI/subgroup/error tabs.
13. **Settings** (`/settings`) → move the Strong/Potential-Fit sliders (live band
    preview) → the new policy governs every subsequent evaluation this session;
    past evaluations keep the thresholds they were scored with.

---

## 13. Known limitations (consolidated, honest)

- **Embedding fallback on constrained machines.** Without loadable
  sentence-transformers weights, `EmbeddingMatcher` silently drops to a
  HashingVectorizer (token-overlap), degrading "semantic" quality — happens on the
  Windows dev box's paging-file limit and in memory-tight environments.
- **Small local LLM.** `qwen2.5:1.5b` gives shallow/broad recommendations; quality
  scales with `OLLAMA_MODEL` on better hardware. Zero-shot, no fine-tuning.
  Hallucination is mitigated (grounding + JSON validation + consistency guard) but
  not eliminated; the guard is a bypassable denylist that only runs for
  REJECT/low-coverage. Layer 2 is optional and CPU-slow (~50 s/run observed).
- **No real labelled dataset.** Layer 1 is benchmarked on **synthetic** data (which
  inflates lexical-overlap methods); Layer 2 has no ground truth and is judged by a
  qualitative rubric, not accuracy.
- **Score-scale discontinuity.** `MatchResult` rows before 2026-09-09 used the
  overfit 0.9/0.0/0.1 checkpoint and understated experience/coverage; not
  retroactively recomputed.
- **Accepted security items:** upload size/type validation (M-1), DOCX XXE on the
  fallback path (M-2), LLM prompt-injection into advisory text (M-3), unescaped
  reportlab markup (L-1), weak password policy + no login lockout (L-3/L-4),
  Next.js < 16 advisories (H-2).
- **Deployment:** no 24/7 hosting; the Azure/Vercel split is unconfigured in the
  repo, and the shipped compose wires the deprecated Streamlit frontend.
- **Modelling/quality debt:** global-unique `Candidate.email`; dead explainer/PDF
  fallback branches; 6 stale legacy-API tests failing; corrupted `requirements.txt`
  trailing line; substantial root-level dev
  scatter and 22 DB backups committed.

---

## 14. Glossary

- **TF-IDF** — Term Frequency–Inverse Document Frequency: weights a term by how
  often it appears in a document, discounted by how common it is across all
  documents. Here it vectorises CV and JD for a lexical-overlap score.
- **Cosine similarity** — cosine of the angle between two vectors; 1 = identical
  direction, 0 = orthogonal. Used to compare TF-IDF and embedding vectors.
- **Embedding** — a dense numeric vector capturing a text's meaning, so
  semantically similar texts sit close together.
- **SentenceTransformer / MPNet / MiniLM** — pretrained neural models that turn a
  sentence into an embedding (`all-mpnet-base-v2` = higher quality;
  `all-MiniLM-L6-v2` = lighter; the multilingual variant handles EN+FR).
- **HashingVectorizer** — a stateless text vectoriser that hashes n-grams into a
  fixed sparse space; JobTest's lower-accuracy fallback when embeddings can't load.
- **n-gram** — a contiguous run of *n* tokens ("machine learning" = a 2-gram).
- **Hybrid fusion** — combining several models' scores with fixed weights into one.
- **AUC-ROC** — Area Under the ROC Curve: probability the model ranks a random
  positive above a random negative; 1.0 = perfect, 0.5 = chance. Threshold-free.
- **Precision / Recall / F1** — precision = of predicted-positives, how many were
  right; recall = of true positives, how many were caught; F1 = their harmonic
  mean at a chosen threshold.
- **Calibrated threshold** — the score cutoff chosen on validation data (here by
  best F1) to convert a continuous score into a yes/no label.
- **McNemar's test** — a paired test of whether two classifiers disagree
  significantly on the same items.
- **Decision confidence (here)** — an *uncalibrated* distance from the nearest
  decision threshold, normalised to [0,1]; **not** a probability of a successful
  hire.
- **Ollama** — a local server that runs open LLMs on your own machine via an HTTP
  API (no cloud).
- **Quantized model** — an LLM whose weights are stored at lower numeric precision
  to shrink RAM/size (e.g. `qwen2.5:1.5b`) at some quality cost.
- **Zero-shot / no fine-tuning** — using a pretrained model as-is, steered only by
  the prompt, with no task-specific retraining.
- **Local-LLM grounded reasoning (RAG-adjacent)** — feeding the model the
  already-computed structured facts and asking it to *interpret* rather than invent
  or re-score.
- **JWT** — JSON Web Token: a signed token proving an authenticated session; here
  HS256-signed, 60-minute expiry.
- **OAuth2 password bearer** — the login flow (username+password → bearer token
  sent as `Authorization: Bearer …`).
- **CORS** — browser rule controlling which web origins may call the API; JobTest
  uses an explicit localhost allow-list.
- **IDOR** — Insecure Direct Object Reference: accessing another user's record by
  guessing its id; prevented here by recruiter-scoped ownership checks.
- **XSS** — Cross-Site Scripting: injecting script into a page; avoided via React's
  auto-escaping (only a static theme script uses `dangerouslySetInnerHTML`).
- **XXE / billion-laughs** — an XML entity-expansion denial-of-service; the DOCX
  zipfile fallback's exposure (finding M-2).
- **bcrypt / passlib** — a slow, salted password-hashing algorithm and the library
  wrapping it.
- **React Three Fiber (R3F) / three.js / drei** — a React renderer for WebGL 3D and
  its helper library, used for the neural field and score torus.
- **Framer Motion** — a React animation library (spring physics, variants,
  shared-layout transitions) powering the platform's motion.
- **App Router (Next.js)** — Next.js's file-system routing under `app/` with nested
  layouts and server/client components.
- **Alembic** — SQLAlchemy's schema-migration tool (present but minimally used;
  most migration is the additive `ensure_schema`).

---

## Appendix A — repository file map (top level)

- **Backend:** `src/` (see §3.3), `scripts/` (`export_production_model.py`,
  `verify_deep_analysis.py`, `test_database.py`), `alembic/` (+ `alembic.ini`).
- **Data/models:** `data/datasets/` (generator, `skills_dictionary.json`,
  `cv_job_dataset.csv`), `data/backups/` (22 `.bak`), `models/checkpoints/
  hybrid.pkl`, `evaluation/results/evaluation_results.json`, `evaluation/figures/`
  (6 PNGs), `notebooks/evaluation.ipynb`.
- **Frontend (current):** `web/` (Next.js — `app/`, `components/`, `lib/`, config).
- **Frontend (legacy, deprecated):** `frontend/` (Streamlit — `app.py` 350 LoC,
  `styles/theme.py` 749 LoC, `components/ui.py` 825 LoC, 10 pages, `decision_state.py`).
- **Deploy:** `Dockerfile.api`, `Dockerfile.frontend`, `docker-compose.yml`,
  `.dockerignore`, `.streamlit/config.toml`.
- **Docs:** `README.md`, `PROJECT_OVERVIEW.md`, `PROJECT_REPORT.md`,
  `TECHNICAL_DOCUMENTATION.md`, `LLM_LAYER.md`, `BUGFIXES.md`, `SECURITY_AUDIT.md`,
  `FUNCTIONAL_AUDIT.md`, `FUNCTIONAL_ARCHITECTURE.md`, `DESIGN_AUDIT.md`,
  `DATA_REDESIGN_AUDIT.md`, `HowToRun.txt`, `web/REBUILD.md`,
  `web/KNOWN_DEVIATIONS.md`, and this `PFE_REPORT.md`.
- **Dev scatter (not shipped):** see §6.5.

## Appendix B — document-vs-code discrepancies found during this audit

These are places where an existing repo document disagrees with the current code;
the thesis should follow the code:

1. `TECHNICAL_DOCUMENTATION.md` still describes the platform as **stateless / no
   database** and **Streamlit** as the frontend, and lists default hybrid weights
   **0.50/0.30/0.20** and default English embedding **all-MiniLM-L6-v2**. The code
   is: **SQLAlchemy-persisted**, **Next.js** frontend, weights **0.2/0.4/0.4**,
   default English embedding **all-mpnet-base-v2**.
2. `TECHNICAL_DOCUMENTATION.md` states the critical-skill penalty is **0.10**; the
   code (`skill_matcher.py`) applies **up to 0.20**.
3. `PROJECT_OVERVIEW.md` and the Settings "About" panel still brand the product
   **NeuralHire** (the superseded prototype, since renamed) and version it **v4.0** / "Enterprise SaaS … Streamlit"; the API
   version string is **2.0.0**; the product is now **JobTest** with a Next.js UI.
4. `embedding_model.py`'s docstring claims `all-MiniLM-L6-v2` is the default while
   its own code reads the default from config, which is `all-mpnet-base-v2`.
5. `HowToRun.txt` / `README.md` still lead with Streamlit run instructions; the
   supported frontend is the Next.js app in `web/`.
6. The Azure/Vercel deployment topology is described in prose but has **no
   configuration in the repository**, and `docker-compose.yml` wires the legacy
   Streamlit frontend rather than Next.js.

*End of report.*
