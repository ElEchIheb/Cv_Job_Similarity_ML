# JobTest — Project Report (AI/ML Focus)

## 1. Project Overview

JobTest is an enterprise-grade AI Recruitment and Talent Intelligence Platform designed to automate the screening, analysis, and ranking of candidates. The platform serves HR professionals and recruiters by removing the subjectivity of manual screening and accelerating the recruitment pipeline.

**Core Workflow:**
1. A recruiter uploads a candidate's CV (PDF/DOCX) or pastes its text, and selects an existing job offer.
2. The AI matching engine processes both the CV and job description to compute a compatibility score across multiple dimensions (Semantic, Keyword, Skills).
3. The platform applies configurable thresholds to yield a clear hiring decision (HIRE, CONSIDER, or REJECT) along with a confidence metric and a justification/action plan.

**High-Level Architecture:**
- **Frontend (Next.js)**: A refined, dark-glassmorphism web interface providing dashboards, leaderboards, and detailed analytics.
- **Backend (FastAPI)**: A stateless REST API serving both core endpoints and additive `/ui` parity endpoints. The additive `/ui` router acts as a bridge, allowing the Next.js app to consume exactly the same backend logic, thresholding, and persistence layers that the legacy Streamlit app used, without re-implementing business logic in the browser.
- **AI/Matching Engine (Python)**: The core intelligence layer powered by `scikit-learn` and `sentence-transformers`, orchestrating multiple NLP techniques.
- **Database (SQLite + SQLAlchemy)**: Persists candidates, job offers, and evaluation history locally.

**Tech Stack & Local Deployment:**
- **Languages & Frameworks**: Python 3.10+ (3.11 recommended, 3.13 requires `TOKENIZERS_PARALLELISM=false` to avoid crashes), FastAPI, Next.js (React), Tailwind CSS, SQLite, SQLAlchemy.
- **AI Libraries**: `sentence-transformers`, `scikit-learn`, `spacy` (optional).
- **Running Locally**:
  - **Backend**: Run `uvicorn src.api.main:app --port 8000` from the project root. (Requires a `.env` file containing `JWT_SECRET_KEY`, `ALLOWED_ORIGINS`, etc.)
  - **Frontend**: Navigate to `web/` and run `npm install && npm run dev` to start on port 3000. (Requires `web/.env.local` configured with `NEXT_PUBLIC_API_BASE=http://localhost:8000/api/v1`).
  - **Docker**: A `docker-compose.yml` is provided to spin up both containers.

---

## 2. AI / Matching Engine

This is the core evaluation pipeline of JobTest. It orchestrates three independent scoring models which are then fused into a hybrid result.

### a) Keyword Relevance (`TFIDFMatcher`)
- **Algorithm/Library**: Term Frequency-Inverse Document Frequency (TF-IDF) via `sklearn.feature_extraction.text.TfidfVectorizer` (scikit-learn).
- **Text Preprocessing**: The inputs to `TFIDFMatcher.predict` are raw text strings (the raw CV and job description). While JobTest has a `clean_text` utility in `src/parsing/parser.py`, the `TFIDFMatcher` in `src/models/tfidf_model.py` operates directly on raw text. It configures the vectorizer with `ngram_range=(1, 3)`, `max_features=10000`, `min_df=2`, and `sublinear_tf=True`. It does not explicitly strip stopwords or handle languages internally; it relies on scikit-learn's default tokenization.
- **Comparison Metric**: The vectorized CV and job description are compared using **cosine similarity** (`sklearn.metrics.pairwise.cosine_similarity`).
- **Output**: The raw cosine similarity score is a float clipped to the `[0.0, 1.0]` range. It is translated to a percentage by multiplying by 100.

### b) Semantic Relevance (`EmbeddingMatcher`)
- **Embedding Models**: Uses `SentenceTransformer`. The default English model is `all-MiniLM-L6-v2` (384-dimensional embeddings), and the multilingual model is `paraphrase-multilingual-mpnet-base-v2` (768-dimensional). The English model can be overridden to `all-mpnet-base-v2` via the `EMBEDDING_MODEL_EN` environment variable.
- **Fallback Behavior**: If `sentence-transformers` is uninstalled or fails to load (e.g., due to Windows paging-file/memory limits crashing the threaded model materializer on Python 3.13), the platform falls back to `_LocalEmbeddingBackend`. This fallback utilizes `sklearn`'s `HashingVectorizer`, vertically stacking word n-grams (1-2) and character n-grams (3-5) into a highly sparse 4096-dimensional space (L2-normalized). Unlike true dense semantic embeddings that capture meaning and context, this fallback only measures exact sub-string/token overlaps, fundamentally altering the nature of the "Semantic Relevance" score to resemble an advanced keyword matcher.
- **Similarity Computation**: For the primary calculation, text is vectorized using both English and multilingual models. Similarity is the **cosine similarity** between the CV and Job embeddings.
- **Score Scaling**: 
  - `base_score` = 50% English similarity + 50% multilingual similarity.
  - `section_score` = A weighted similarity comparing specific CV sections (parsed via regex headers) against the full job description. Weights: Experience (40%), Skills (30%), Summary (15%), Education (10%), Languages (5%).
  - The final semantic score is `0.7 * base_score + 0.3 * section_score` (clipped to `[0.0, 1.0]`).

### c) Skills Assessment (`SkillMatcher` & `SkillExtractor`)
- **Extraction Mechanism**: Text is aggressively cleaned of artifacts (URLs, emails, punctuation) via `src/parsing/parser.py`. The `SkillExtractor` relies on:
  1. A static dictionary lookup (`data/datasets/skills_dictionary.json`) using pre-compiled exact-match regex patterns and alias mapping (e.g., "ml" -> "machine learning").
  2. Rule-based NER using `spaCy`'s `EntityRuler` (if installed) to locate tools, frameworks, and languages.
  3. 1-to-3-gram sliding windows checked against the dictionary.
- **Categorization Logic**:
  - **Detected & Matching Skills**: The intersection of skills extracted from the CV and the job description.
  - **Additional (Extra) Skills**: Skills present in the CV but absent from the job description (`cv_skills - job_skills`).
  - **Missing Skills**: Skills present in the job description but absent from the CV (`job_skills - cv_skills`).
  - **Priority Gap (Critical Missing)**: The job description is split into fragments. If a missing skill appears in the same sentence as triggers like "required", "must", "mandatory", or "indispensable", it is escalated to a "critical" priority gap.
- **Scoring**:
  - `hard_score` = overlap ratio (matching hard skills / total required hard skills).
  - `soft_score` = overlap ratio (matching soft skills / total required soft skills).
  - The `base_score` is a weighted average (70% hard skills, 30% soft skills).
  - Bonuses are added for domain alignment (+5%) and relevant certifications (up to +10%). 
  - A penalty is applied based on missing critical skills (-20% * proportion of missing critical skills). 

### d) Overall AI Match (Hybrid)
- **Score Formula**: The `HybridMatcher` fuses the three individual scores using a weighted sum. The default weights are `0.2` (Keyword/TF-IDF), `0.4` (Semantic/Embedding), and `0.4` (Skills). 
- **Configuration**: The weights are determined dynamically during the training/evaluation phase via a grid search on the validation set (`optimize_weights`) to maximize AUC-ROC. The production weights are baked into the `hybrid.pkl` checkpoint (which, in a recent evaluation, leaned heavily towards TF-IDF at 0.9). If no checkpoint dictates otherwise, it defaults to the 0.2/0.4/0.4 split.

### Decision Engine
- **Classification Logic**: Controlled strictly by the canonical `DecisionEngine` (`src/decisioning/decision_engine.py`). Given a percentage score:
  - `score >= strong_fit_threshold` → **HIRE** ("Strong Fit")
  - `potential_fit_threshold <= score < strong_fit_threshold` → **CONSIDER** ("Potential Fit")
  - `score < potential_fit_threshold` → **REJECT** ("Low Fit")
- **Thresholds**: Defined in the recruiter's active session state (configured via the Settings page). The defaults are 75.0 for Strong Fit and 55.0 for Potential Fit. Changing them only affects *future* evaluations. Past evaluations persist their exact configuration metadata to guarantee reproducibility.
- **Confidence Score**: An uncalibrated distance metric representing how safely the score sits inside its classification band. Formula: `nearest_distance_to_a_threshold / 20.0` (clamped to `[0.0, 1.0]`). It translates to nominal bands: High (≥ 0.66), Medium (≥ 0.33), Low (< 0.33). It is explicitly **not** a probability of hiring success.
- **5-Axis Radar Chart**: 
  - *Technical*: `skill_score * 100`
  - *Semantic*: `embedding_score * 100`
  - *Experience*: `min(100, (candidate_years / required_years) * 100)`
  - *Soft Skills*: `min(100, length(cv_soft_skills) * 20)`
  - *Domain*: 90 if domains match, 50 otherwise.

### Model Provenance & Evaluation
- **Provenance**: There is no fine-tuning of embedding weights. Pre-trained weights (`all-MiniLM-L6-v2` and `paraphrase-multilingual-mpnet-base-v2`) are downloaded transparently via HuggingFace. The TF-IDF and Hybrid fusion weights are trained locally and serialized into `models/checkpoints/hybrid.pkl`.
- **Benchmark Data (`evaluation_results.json`)**: Generated by `EvaluationSuite`. It contains test set metrics (Accuracy, Precision, Recall, F1, AUC-ROC, inference latency). AUC-ROC indicates how well the model separates suitable from unsuitable candidates across all possible thresholds. F1 measures harmonic mean of precision and recall at the optimal threshold.
- **Known Limitations & Biases**: 
  - *Memory Exhaustion*: The `sentence-transformers` library on Windows under Python 3.13 crashes when threaded loading is enabled. Bypassing it can lead to memory exhaustion limits, causing a silent fallback to `HashingVectorizer` which vastly degrades semantic relevance to a mere token-overlap calculation.
  - *Data Drift*: The `evaluation_results.json` acts as a static snapshot. It does not automatically update as new candidates flow through the system.
  - *Language constraints*: Stemming and lemmatization heavily assume English or French contexts.
  - *Rigid Skill Dictionary*: Skills not present in `skills_dictionary.json` are entirely blind spots to the NER pipeline unless coincidentally picked up by semantic embeddings.

---

## 3. Data Model

The application utilizes SQLAlchemy connected to a SQLite database. All major entities are heavily relational and scope to individual recruiters (`recruiter_id`).

- **`User`**: Recruiter accounts containing `email`, `hashed_password`, and `role`.
- **`Candidate`**: Contains candidate PII (`full_name`, `email`, `phone`), `recruiter_id`, pipeline `status` (NEW, INTERVIEW, etc.), and `is_anonymous` flags. Has a 1:N relationship with `CV` and `MatchResult`.
- **`JobOffer`**: Defined by `job_code`, `title`, `description`, `required_skills_raw`, `recruiter_id`, and a lifecycle `status` (OPEN, CLOSED).
- **`MatchResult`**: The canonical evaluation record. Contains relationships to both `Candidate` and `JobOffer`. Persists the computed metrics (`final_score`, `score_hybrid`, `score_semantic`, `score_keyword`, `score_skill`), the decision (`HIRE`/`CONSIDER`/`REJECT`), uncalibrated `decision_confidence`, and the active configuration (`strong_fit_threshold`, `potential_fit_threshold`) at the time of evaluation to guarantee reproducibility. Also stores full explainability payloads as serialized JSON in `explanation_json`.

**Persistence Rules:** Batch and single evaluations via Candidate Analysis are persisted as `MatchResult`s. "AI Insights" side-by-side model comparisons operate purely in-memory and are never persisted to the DB.

---

## 4. Backend API Surface

The backend exposes primary API routes under `/api/v1` and additive UI routes under `/api/v1/ui`.

**Primary API:**
- `GET /api/v1/health[/detailed]`: Liveness, version, and model diagnostic statuses.
- `GET /api/v1/metrics`: Internal telemetry/usage statistics.
- `POST /api/v1/match[/file]`: CV text/file matching payload directly.
- `POST /api/v1/rank`: Rank multiple candidate dictionaries against one job.
- `POST /api/v1/report/pdf`: Generates an enterprise PDF report via `reportlab` from an evaluation payload.

**UI Parity API (`/api/v1/ui`)** — Exposes business logic to Next.js without duplication:
- `GET /ui/overview`: Recruiter-scoped dashboard statistics.
- `GET/POST/PUT/DELETE /ui/job-offers` & `GET/PUT/DELETE /ui/candidates`: CRUD for jobs and candidates, locked to the authenticated `recruiter_id`. Cannot hard-delete entities with active matches.
- `GET /ui/matches[/id]`: Fetch historical evaluations and deep-dive JSON payloads.
- `POST /ui/evaluate[/file]`: Wraps the internal `evaluate_and_persist` logic using the current session's custom thresholds.
- `POST /ui/compare`: In-memory evaluation comparing all 4 distinct models on the same text.
- `GET /ui/quality[/figures]`: Reads and streams the offline `evaluation_results.json` benchmark files.

**Auth Flow & CORS:**
- **Auth**: Standard OAuth2 Password Bearer flow yielding a JSON Web Token (JWT).
- **Token Lifetime**: 60 minutes (`JWT_ACCESS_TOKEN_EXPIRE_MINUTES`). 
- **CORS**: Configured rigidly via `ALLOWED_ORIGINS` (defaults to `http://localhost:8501,http://localhost:3000`). Supports GET, POST, PUT, DELETE, PATCH, OPTIONS.

---

## 5. Frontend Architecture

The frontend is a completely functional Next.js App Router application mirroring the legacy Streamlit platform, styled with an enterprise "Precision Intelligence" design language.

**Page Inventory:**
1. `/login`: Authentication gate (`POST /auth/login`).
2. `/overview`: Global telemetry and funnel KPIs (`GET /ui/overview`, `GET /ui/matches`).
3. `/analysis`: The flagship evaluation interface. Upload CVs, pick jobs, render radar charts and skill gaps (`POST /ui/evaluate/file`, `POST /api/v1/report/pdf`).
4. `/leaderboard`: Rank N resumes against 1 job description (`POST /ui/evaluate/file`).
5. `/history`: Tabular view of all historical match analyses (`GET /ui/matches`).
6. `/jobs`: Manage job postings (`GET/POST/PUT /ui/job-offers`).
7. `/candidates`: Manage candidate CRMs (`GET/PUT/DELETE /ui/candidates`).
8. `/insights`: Compares scoring models dynamically (`POST /ui/compare`).
9. `/quality`: Visualizes static benchmarking results (`GET /ui/quality`).
10. `/settings`: Modifies active thresholds stored in client state.

**Design System:**
- **Tokens**: Theme-varying variables defined in `globals.css` and mapped natively into `tailwind.config.ts` (`bg-canvas`, `bg-surface`). Includes a non-inverted dual palette ensuring light and dark themes exist as first-class citizens.
- **Palette**: Deep slate surfaces, vibrant brand accents (violet, cyan, magenta), and semantic stat hues (success, warning, danger).
- **Motion**: Driven by `framer-motion` for spring-loaded reveals and transitions, avoiding overly heavy "gaming" pulses.
- **3D Elements**: Uses `@react-three/fiber` and `@react-three/drei` to render subtle ambient geometries like `NeuralField` (login parallax) and `ScoreTorus` (visualizing evaluation scores).

**Known Deviations from Legacy Code:**
1. **Recruiter Scoping**: All dashboards, histories, and lists are rigidly scoped to the active `recruiter_id`. Users only see data they own.
2. **AI Insights Persistence**: The model comparison page explicitly bypasses database persistence to prevent polluting candidate history with overlapping evaluations.

---

## 6. Current Status & Known Issues

- **Verified Live**: The Next.js rebuild has achieved 100% functional parity with the FastAPI backend. Authentication, CRUD workflows, Candidate Analysis, Leaderboards, Settings configuration, and PDF generation are fully tested and functional. 
- **Pending/Tech Debt**: No major functionality remains pending. However, the system relies on legacy Python ML dependency resolution which is inherently fragile.
- **Quirks & Issues**: 
  - *JWT Expiration*: Tokens expire unconditionally after 60 minutes, which can abruptly interrupt heavy ranking sessions. 
  - *Windows Embedding Paging Issue*: Deep semantic analysis frequently exhausts available memory on Windows running Python 3.13, causing an opaque fallback to the uncalibrated `HashingVectorizer`.

---

## 7. Glossary

- **TF-IDF**: *Term Frequency-Inverse Document Frequency*. A statistical measure used to evaluate how important a word is to a document in a collection.
- **Embeddings**: Dense numerical vectors representing the semantic meaning of text. 
- **Cosine Similarity**: A metric used to measure how similar two text embeddings are, regardless of their size, by calculating the cosine of the angle between them.
- **HashingVectorizer**: A less accurate fallback text vectorization technique that relies on hashing token counts directly into a sparse matrix, used when robust embedding models crash.
- **AUC-ROC**: *Area Under the Receiver Operating Characteristic Curve*. A performance measurement for classification problems denoting the model's capability of distinguishing between classes across multiple thresholds.
- **Confidence Score**: In this platform, an uncalibrated geometric measure indicating how decisively a candidate's percentage score sits within its assigned decision band (Hire/Consider/Reject). 
- **JWT**: *JSON Web Token*. The cryptographic standard used by the platform to manage and verify recruiter login sessions securely.
