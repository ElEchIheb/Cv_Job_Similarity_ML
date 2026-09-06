# NeuralHire — Technical Documentation

## 1. General Project Presentation

### Project Name
**NeuralHire** (also referred to as **JobTest AI Platform**)

### Problem Addressed
Recruiters and Human Resource (HR) departments process hundreds of Curriculum Vitaes (CVs) for each job opening. Traditional resume screening is highly manual, prone to cognitive bias, and slow. Simple keyword matching often fails to grasp the semantic context of a candidate's experience, resulting in missed talent or poor hires.

### Context & Objectives
NeuralHire is developed to solve the resume-filtering problem using modern Natural Language Processing (NLP) and Artificial Intelligence. The system's primary goals are:
1. **Accelerated Filtering**: Minimize screening time by automatically sorting and ranking candidates.
2. **Context-Aware Semantic Matching**: Go beyond exact keyword matches to understand synonyms, domains, and thematic similarities.
3. **Structured Explainability**: Deliver detailed, readable justifications, radar charts, and recommendation paths to explain *why* a candidate fits or does not fit.
4. **GDPR Compliance**: Process all CVs in-memory, avoiding the storage of sensitive candidate datasets on a database.

### Target Users & Actors
- **Recruiter / HR Specialist**: The primary operator. Uploads CVs, inputs Job Descriptions (JDs), inspects radar analyses, downloads PDFs, and views rankings.
- **Candidate**: The subject of evaluation. Their resumes (PDF/DOCX) are parsed and evaluated.
- **Administrator / QA Engineer**: Monitors API usage, runs model validation metrics, and tunes AI model weights.

### Complete Business Workflow
1. A recruiter defines the role requirements (Job Description) and inputs it.
2. The recruiter uploads a candidate's resume (PDF or DOCX).
3. The platform processes the text, extracts skills, calculates semantic alignment, and generates a score.
4. The recruiter views the decision report, downloads a PDF copy for the hiring team, or reviews a ranked leaderboard of all applicants.

---

## 2. Global Architecture

### Architecture Layers

#### Frontend Layer (Presentation)
- **Technology**: Streamlit v1.55.0.
- **Role**: Render pages, handle uploads, display dashboard statistics, show radarcharts, and handle route-based navigation.
- **Design System**: A dark enterprise layout featuring glassmorphism, responsive elements, Material symbols, and custom CSS overrides injected on startup.

#### Backend Layer (Application Server)
- **Technology**: FastAPI (running on Uvicorn).
- **Role**: Serve REST API endpoints, validate input schemas via Pydantic, manage rate-limiting, and orchestrate parsing and scoring models.

#### AI & NLP Layer (Intelligent Processing)
- **Technologies**: SentenceTransformers, Scikit-Learn, spaCy, NLTK-like tokenizers.
- **Pipeline Components**: 
  - Text Cleaners (removing emails, phone numbers, urls, multi-line spacing).
  - Skill Extractor (regular expressions, n-grams, word alias expansion, and rule-based NER).
  - TF-IDF Matcher (character & n-gram frequency).
  - Semantic Embedding Matcher (Cosine similarity over SentenceTransformer vectors).
  - Hybrid Scorer (normalizes and merges individual model outputs).

#### Data Layer (Stateless Storage)
- **Engine**: Zero-State Storage (Stateless). 
- **Reasoning**: NeuralHire handles data entirely in memory. It uses local files (`skills_dictionary.json` as a dictionary base) and generates PDFs on-the-fly without database servers, providing structural security and compliance.

#### Deployment Layer (Containerization)
- **Containers**: Isolated Frontend and Backend Docker containers.
- **Orchestration**: Docker Compose configured to run Backend on port `8000` and Frontend on port `8501`.

### Data Flow
```
  [User Uploads CV] (PDF/DOCX)
         │
         ▼
  [Document Parsing] (pdfplumber page text flow / docx paragraph extract)
         │
         ▼
  [Text Cleaning] (URLs, emails, phones removed; text lowercased)
         │
         ▼
  [Skill Extraction] (Dictionary matches + N-Grams + SPAEntityRuler)
         │
         ▼
  [AI Analysis & Model Comparison]
    ├── TF-IDF Vectorizer (Character 1-3 Gram Frequency)
    ├── SentenceTransformers (all-MiniLM-L6-v2 Embeddings)
    └── Skill Matcher (Hard/Soft Skill overlap coefficients)
         │
         ▼
  [Hybrid Score Generation] (Weighted blend of component scores)
         │
         ▼
  [Explanation & Recommendation Engine] (Verdict justification & roadmap link generation)
         │
         ▼
  [Report Generation] (Generate & download PDF)
```

---

## 3. Frontend Documentation

### Framework: Streamlit
Streamlit v1.55.0 was chosen to provide rapid, interactive UI rendering directly from Python. It enables reactive state bindings and integrates with Python graphics libraries (Matplotlib, Seaborn) without requiring complex React/Vue frontend boilerplate.

### Folder Structure
- `frontend/app.py`: Main entry point, routes navigation, handles layout frames.
- `frontend/styles/theme.py`: Custom CSS definitions (`PREMIUM_CSS`), inline SVG assets (`ICONS`).
- `frontend/components/ui.py`: UI components (radar charts, stat widgets, skill chips).
- `frontend/pages/`: Individual modular views:
  - `dashboard.py`: System usage, health checkpoints.
  - `single_match.py`: Direct match workflow.
  - `ranking.py`: Multiple candidate comparisons.
  - `model_comparison.py`: Side-by-side model differences.
  - `batch_analysis.py`: Batch evaluation page.
  - `evaluation_metrics.py`: Testing and quality review page.
  - `settings.py`: Platform configuration settings.

### Interface Details

#### 1. Executive Dashboard (`dashboard.py`)
- **Purpose**: Displays system performance metrics.
- **KPIs**: Requests processed, current latency (ms), model status (healthy vs degraded).
- **UX**: Displays high-level cards with glowing neon indicators and real-time backend endpoint metrics.

#### 2. Candidate Analysis (`single_match.py`)
- **Purpose**: Single candidate screening.
- **Widgets**: Drag-and-drop file uploader, model selection picker, job description text area.
- **Visualizations**: 
  - Interactive Skill Radar (comparing Candidate capabilities vs Job requirements).
  - Glowing match rings for overall percentage score.
  - Color-coded skill chips: green (matched), blue (extra), red (missing), purple (critical missing).
  - "Generate PDF" download button.

#### 3. Talent Ranking (`ranking.py`)
- **Purpose**: Display a leaderboard of multiple candidates compared against a single job description.
- **Visualizations**: Sorted tables with individual decision labels ("HIRE", "CONSIDER", "REJECT") and matching key skills.

#### 4. UI/UX Customization Shell
Streamlit's default UI styling is completely overwritten by injecting `PREMIUM_CSS` from `theme.py` using `st.markdown(..., unsafe_allow_html=True)`.
Key features include:
- **Cinematic Backgrounds**: Radial gradients combined with a subtle CSS grid animation.
- **Glassmorphism**: Panels styled with semi-transparent dark backgrounds (`rgba(12, 22, 40, 0.88)`), subtle cyan borders, and `backdrop-filter: blur(16px)`.
- **Custom Navigation Shell**: Replaces Streamlit's native sidebar navigation with custom button navigation styled with Lucide SVG icons.
- **Floating Reopen Button**: The native sidebar toggle remains accessible when collapsed via a custom absolute selector (`button[aria-label="open sidebar" i]`) that is styled to match the dark theme and placed in the top-left corner.

---

## 4. Backend Documentation

### Framework: FastAPI
FastAPI was selected for its performance, asynchronous request capabilities, and automatic swagger/OpenAPI documentation generation (available at `/api/v1/docs`).

### Folder Architecture
- `src/api/main.py`: FastAPI server setup, rate limiting, and route definitions.

### API Endpoints

#### Health Check (`GET /api/v1/health`)
- **HTTP Method**: GET
- **URL**: `/api/v1/health`
- **Purpose**: Liveness probe.
- **Output**: 
  ```json
  {
    "status": "ok",
    "version": "2.0.0",
    "models": ["embedding", "hybrid", "skill", "tfidf"],
    "timestamp": 1790000000.0
  }
  ```

#### Detailed Health Status (`GET /api/v1/health/detailed`)
- **HTTP Method**: GET
- **URL**: `/api/v1/health/detailed`
- **Purpose**: Inspect model loading statuses and usage stats.
- **Output**: Returns JSON containing `"model_status"`, `"config"`, and `"usage"`.

#### Single Match (`POST /api/v1/match`)
- **HTTP Method**: POST
- **URL**: `/api/v1/match`
- **Input**:
  ```json
  {
    "cv_text": "Python developer. Skills: Python, Django, PostgreSQL, Docker.",
    "job_text": "Backend developer: Python, Django, PostgreSQL required. Docker preferred.",
    "model": "hybrid"
  }
  ```
- **Output**:
  ```json
  {
    "score": 0.825,
    "percentage": 82.5,
    "label": 1,
    "confidence": "high",
    "component_scores": {
      "tfidf_score": 0.54,
      "embedding_score": 0.89,
      "skill_score": 0.95
    },
    "explanation": {
      "verdict": "Strong Match",
      "hiring_recommendation": {
        "decision": "HIRE",
        "justification": "Candidate demonstrates strong alignment..."
      }
    }
  }
  ```

#### Match File (`POST /api/v1/match/file`)
- **HTTP Method**: POST
- **URL**: `/api/v1/match/file`
- **Input**: `cv_file` (Binary Multipart), `job_text` (Form string), `model` (Form string).
- **Purpose**: Directly uploads PDF/DOCX files, parses them in-memory, and scores them.

#### Rank Candidates (`POST /api/v1/rank`)
- **HTTP Method**: POST
- **URL**: `/api/v1/rank`
- **Input**: `job_text` (string), `candidates` (List of `{cv_text, name}` objects).
- **Output**: Ranked array sorted by score.

#### PDF Report Generation (`POST /api/v1/report/pdf`)
- **HTTP Method**: POST
- **URL**: `/api/v1/report/pdf`
- **Input**: Results, Explanations, and Recommendations JSON payloads.
- **Output**: A raw PDF binary block (`application/pdf`) generated on-the-fly.

---

## 5. Artificial Intelligence Module

### Document Preprocessing & Parsing
- **PDF Extraction**: Done via `pdfplumber`. Features a **two-column layout parser** that splits pages down the center and groups words by horizontal and vertical coords, avoiding mixed paragraphs.
- **DOCX Extraction**: Extracts paragraph texts and tables, falling back to a raw XML zipfile reader if the `python-docx` library fails.
- **Text Cleaning**: `clean_text()` removes emails, websites, phone numbers, and multi-line breaks, returning lowercased strings.

### NLP Processing
- **Lemmatization & Normalization**: Done natively via `spaCy` (if a model is installed) or falls back to `_naive_lemma()` which strips standard endings (`-ing`, `-ed`, `-ations`, etc.) while protecting technical terms like `C++`, `C#`, and `.net`.
- **Skill Extraction**: Combined search pipeline:
  - **Dictionary Match**: Compares text against `skills_dictionary.json` using pre-compiled regex patterns.
  - **NER Pipeline**: Utilizes spaCy's `entity_ruler` to extract skills and certifications.
  - **N-Grams**: Iterates through 1, 2, and 3-word combinations to detect multi-word skills (e.g., "deep learning", "rest api").

### Model Details

#### TF-IDF Matcher (`tfidf_model.py`)
- **Method**: Generates TF-IDF matrices (ngram range 1-3, max features 10000, sublinear TF scaling).
- **Purpose**: Measures word-frequency similarity between CV and JD.
- **Formula**: `CosineSimilarity(CV_tfidf, JD_tfidf)`

#### Semantic Embedding Matcher (`embedding_model.py`)
- **Method**: Utilizes HuggingFace `SentenceTransformers` (`all-MiniLM-L6-v2` as standard). If unavailable, falls back to a sparse `HashingVectorizer` representation.
- **Section-Aware Scoring**: Segments the CV (Experience, Skills, Education, Languages, Summary) and calculates cosine similarity against the job description with specific weights:
  - **Experience**: 40%
  - **Skills**: 30%
  - **Summary**: 15%
  - **Education**: 10%
  - **Languages**: 5%
- **Final Embedding Score**: `0.7 * Global_Similarity + 0.3 * Section_Aware_Similarity`

#### Skill Matcher (`skill_matcher.py`)
- **Method**: Calculates set overlap values.
- **Hard Skills**: `HardOverlap = len(CV_hard & Job_hard) / len(Job_hard)` (Weighted at 70%)
- **Soft Skills**: `SoftOverlap = len(CV_soft & Job_soft) / len(Job_soft)` (Weighted at 30%)
- **Critical Gaps**: Searches for keywords in sentences containing "required", "must", "essential" in the JD. If any critical skills are missing, it applies a **0.10 penalty**.
- **Bonuses**: Applies a **0.05 bonus** if candidate domain matches the job domain, and a **0.03 bonus** per relevant certification.
- **Formula**: `Overlap_Score = 0.7 * HardOverlap + 0.3 * SoftOverlap + Domain_Bonus + Cert_Bonus - Critical_Penalty`

### Hybrid AI Score Calculation
The final match score is calculated in `HybridMatcher.predict` using a weighted blend:
$$\text{Final Score} = w_{\text{embedding}} \cdot S_{\text{embedding}} + w_{\text{skill}} \cdot S_{\text{skill}} + w_{\text{tfidf}} \cdot S_{\text{tfidf}}$$

By default, the weights are defined as:
- $w_{\text{embedding}} = 0.50$ (Semantic context)
- $w_{\text{skill}} = 0.30$ (Direct skill alignment)
- $w_{\text{tfidf}} = 0.20$ (Lexical match)

The final score is clipped between `0.0` and `1.0`.

---

## 6. AI Explainability

### Verdict Rules
Evaluated scores map to structured HR decisions:
- **$\ge$ 80% (No critical gaps)**: **HIRE** — "Candidate demonstrates strong alignment..."
- **60% - 79% (No critical gaps)**: **HIRE** — "Candidate shows good alignment..."
- **60% - 79% (Has critical gaps)**: **CONSIDER** — "Candidate fits but misses critical skills: [list]..."
- **45% - 59%**: **CONSIDER** — "Candidate is a partial fit..."
- **< 45%**: **REJECT** — "Candidate score is below threshold..."

### Actionable Recommendations
The platform converts gap analysis into developmental recommendations using a static domain-resource mapping:
- If `FastAPI` is missing, it links to `https://fastapi.tiangolo.com/`.
- Calculates estimated weeks needed to learn the missing skills.
- Predicts potential score if gaps are addressed.

---

## 7. Database Documentation

### Zero-State/Stateless Storage Model
NeuralHire does not use a persistent database engine (such as PostgreSQL or SQLite).
- **Text Parsing**: CVs uploaded are parsed, scored, and returned in-memory.
- **GDPR Compliance**: Resumes contain highly sensitive personal data. By not storing files or candidate text databases, NeuralHire guarantees data privacy by design.

---

## 8. APIs and External Technologies

| Scope | Technology / Library | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Frontend** | Streamlit | $\ge 1.41.0$ | UI Dashboard & Navigation |
| **Frontend** | Matplotlib / Seaborn | $\ge 3.9.0$ | Skill Radarchart Rendering |
| **Backend** | FastAPI | $\ge 0.115.0$ | API Server Routing |
| **Backend** | Uvicorn | $\ge 0.32.0$ | Asynchronous ASGI Web Server |
| **AI/NLP** | Sentence-Transformers | $\ge 3.2.0$ | Sentence vector representations |
| **AI/NLP** | spaCy | $\ge 3.8.0$ | Named Entity Recognition (NER) |
| **AI/NLP** | Scikit-Learn | $\ge 1.5.0$ | TF-IDF & Cosine Similarity |
| **Parsing** | pdfplumber | $\ge 0.11.0$ | High-fidelity PDF extraction |
| **Reporting** | ReportLab | $\ge 4.2.0$ | Dynamic PDF report generation |

---

## 9. Docker & Deployment

### Containers
1. **API Container**: Built from `Dockerfile.api`. Installs CPU-optimized Torch, downloads dependencies, and hosts FastAPI via Uvicorn on port `8000`.
2. **Frontend Container**: Built from `Dockerfile.frontend`. Launches the Streamlit app on port `8501`.

### Docker Compose Configuration
The `docker-compose.yml` configures service links so the frontend depends on the API container:
```yaml
services:
  api:
    image: pfe_ai-api:latest
    ports:
      - "8000:8000"
  frontend:
    image: pfe_ai-frontend:latest
    ports:
      - "8501:8501"
    depends_on:
      - api
```

---

## 10. Security

- **Rate Limiting**: Backend tracks requests per IP. Limit is configured to `60` requests per minute.
- **CORS Policies**: Restricted origins are loaded from environment variables (`ALLOWED_ORIGINS` defaults to `localhost:8501` and `localhost:3000`).
- **Temporary File Disposal**: Uploaded resumes are written to temporary files and immediately deleted via a `try...finally` block.

---

## 11. Performance

- **Caching**: AI model loadings are cached using `@st.cache_resource`. The embedding vector cache limits itself to `1024` entries using a FIFO eviction policy.
- **Thread Management**: Tokenizer multi-threading is disabled (`TOKENIZERS_PARALLELISM=false`) to prevent CPU crashes.

---

## 12. Testing

The platform includes a robust test suite powered by `pytest`:
- `test_parsing.py`: Verifies PDF/DOCX parser behavior.
- `test_models.py`: Validates cosine similarities and TF-IDF mappings.
- `test_skill_extractor.py`: Checks skill categorizations and experience parser logic.
- `test_api_extended.py`: Simulates client requests and validates FastAPI responses.
- `test_pdf_generator.py`: Verifies PDF output bytes structures.

---

## 13. Functional Requirements Mapping

| Requirement | Implemented | Location | Details |
| :--- | :--- | :--- | :--- |
| **CV Upload** | Yes | [single_match.py](file:///d:/education/pfe/pfe_ai/frontend/pages/single_match.py) | Supported for PDF & DOCX formats |
| **JD Parsing** | Yes | [parser.py](file:///d:/education/pfe/pfe_ai/src/parsing/parser.py) | Extracts text and filters stopwords |
| **Skill Extraction** | Yes | [skill_extractor.py](file:///d:/education/pfe/pfe_ai/src/nlp/skill_extractor.py) | Dictionary + N-Grams + Rule NER |
| **Semantic Match** | Yes | [embedding_model.py](file:///d:/education/pfe/pfe_ai/src/models/embedding_model.py) | Cosine similarity with SentenceTransformers |
| **Hiring Decision** | Yes | [explainer.py](file:///d:/education/pfe/pfe_ai/src/explainability/explainer.py) | Custom recommendations and confidence metrics |
| **Radar Chart** | Yes | [ui.py](file:///d:/education/pfe/pfe_ai/frontend/components/ui.py) | Recharts metrics with Matplotlib |
| **Leaderboard** | Yes | [ranking.py](file:///d:/education/pfe/pfe_ai/frontend/pages/ranking.py) | Sorts multiple CVs by score |
| **REST API** | Yes | [main.py](file:///d:/education/pfe/pfe_ai/src/api/main.py) | FastAPI endpoints for all match operations |
| **Docker Compose** | Yes | [docker-compose.yml](file:///d:/education/pfe/pfe_ai/docker-compose.yml) | Multi-container dev setup |

---

## 14. Current Version Summary (v5.0)

NeuralHire v5.0 introduces a comprehensive design transformation:
- **Dark Glassmorphism UI**: High-contrast, premium interface replacing default admin themes.
- **Stateful Custom Navigation**: Implements an custom button-driven navigation bar using Material Icons.
- **Robust Toggle Button**: Fixes the sidebar collapse mechanism using explicit fixed position and ARIA accessibility labels to prevent overlay collisions.

---

## 15. Future Improvements

1. **LLM Integration**: Supplement embeddings with generative models (like Llama/Claude) for advanced qualitative evaluation.
2. **User Authentication**: Add JWT authentication and tenant-level configurations.
3. **Database Integration**: Support optional cloud-hosted database connectors (e.g. Supabase, PostgreSQL) for recruiters who wish to persist candidate profiles.
