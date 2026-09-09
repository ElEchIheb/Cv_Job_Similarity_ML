# NeuralHire — Layer 2: LLM Qualitative Reasoning (Local, via Ollama)

*Architecture write-up for the thesis / defense. Companion to `PROJECT_REPORT.md`
(which documents Layer 1, the statistical engine).*

---

## 1. Two-layer hybrid architecture

NeuralHire evaluates a candidate in **two complementary layers**:

| | **Layer 1 — Statistical matching** | **Layer 2 — LLM reasoning** |
|---|---|---|
| Nature | Quantitative, deterministic | Qualitative, interpretive |
| Techniques | TF-IDF, sentence embeddings, skills dictionary, hybrid fusion | Pretrained instruction-tuned LLM, zero-shot |
| Output | Compatibility %, HIRE/CONSIDER/REJECT, radar, skill gaps | Narrative career read, red flags, tailored recs, interview Qs, plain-language justification |
| Training | Local TF-IDF + fusion weights; embeddings pretrained | **None** — no fine-tuning |
| Explainability | Feature/component scores | Natural-language synthesis |
| Determinism | Deterministic | Low-temperature, near-deterministic but not guaranteed |
| Failure mode | Always available | **Optional** — degrades gracefully if Ollama is down |

**Layer 2 is strictly additive.** It consumes Layer 1's structured output plus the
raw CV/JD and returns a new top-level payload `ai_deep_analysis`. It never
touches, overrides, or becomes a dependency of the score/decision pipeline. If
Ollama is unavailable, the application behaves exactly as before — the deep
analysis section simply shows an "unavailable" state.

```
CV + JD ──► Layer 1 (statistical)  ──► score, decision, radar, skills   ──► UI (unchanged)
                     │
                     └── structured results ──► Layer 2 (LLM) ──► ai_deep_analysis ──► UI (new section)
                                                     ▲
                                    grounded on Layer 1's numbers (no re-scoring)
```

### Why a second *reasoning* layer instead of training a classifier?

The academic requirement is a genuinely advanced AI capability — deep
interpretation, not just a similarity number. Two paths existed:

1. **Train/fine-tune a supervised model** on (CV, JD, hiring outcome) triples.
2. **Add a pretrained LLM reasoning layer** that needs no labeled data.

We chose (2), for a reason this very project demonstrated concretely: **there is
no real labeled dataset of hiring outcomes**, and training on small/synthetic
data invites exactly the overfitting/leakage failure we already found and fixed
in Layer 1. The production hybrid checkpoint had been "optimized" to weights
`tfidf 0.9 / embedding 0.0 / skill 0.1` with a degenerate `0.04` threshold — an
artifact of grid-searching on a synthetic validation split (see `BUGFIXES.md`,
Bug 4). That is the canonical small-data trap. A pretrained LLM sidesteps it: it
brings broad world knowledge and instruction-following without us fitting any
parameters to a dataset we don't trust.

---

## 2. Model & runtime

- **Runtime:** [Ollama](https://ollama.com) — a local LLM server exposing an
  OpenAI-ish HTTP API at `http://localhost:11434`. Chosen for zero-config local
  inference, a JSON/format-constrained generation mode, and easy model swapping.
- **Default model:** **`qwen2.5:1.5b`** (quantized; ~986 MB download, ~1.4 GB resident
  process in the verified run).

### Model choice rationale (capability vs. hardware)

The verification machine was profiled immediately before the live run: **7.75 GB
RAM, 4 logical CPUs, and 1.96 GB free RAM** under its normal foreground workload.
It is CPU-only for this workload. On that envelope:

- A 3B model has roughly the entire currently free-RAM budget in weights alone;
  it was not risked alongside the application and embedding process. A 7–8B model
  would swap heavily or fail to load.
- **`qwen2.5:1.5b`** is the smallest model that produced a grounded, first-attempt
  schema-valid analysis here. It occupied ~1.4 GB while loaded and completed the
  canonical CPU run in **51.7 s**. The 0.5B variant ran but produced shallow,
  schema-placeholder content, so it is not the shipped default. This latency is
  acceptable because Layer 2 runs **after** the score renders and never blocks it.

The model is **not** hard-coded. `OLLAMA_MODEL` overrides it, so a stronger
defense machine (16 GB+) can run `OLLAMA_MODEL=llama3.1:8b` for higher-quality
narratives with no code change. This is the honest capability/latency trade-off:
we trade some reasoning quality for the ability to actually run locally on modest
hardware, and expose the knob to trade back.

### Setup (reproducible for the defense)

```bash
# 1. Install Ollama (https://ollama.com/download) — Windows/macOS/Linux
# 2. Start the server (installer usually auto-starts it):
ollama serve
# 3. Pull the model:
ollama pull qwen2.5:1.5b
# 4. Verify:
curl http://localhost:11434/api/tags        # lists installed models
```

Backend config (all optional, sane defaults) — via env or `.env`:

| Var | Default | Meaning |
|---|---|---|
| `LLM_ENABLED` | `true` | Master switch for Layer 2 |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server |
| `OLLAMA_MODEL` | `qwen2.5:1.5b` | Model tag |
| `OLLAMA_TIMEOUT` | `120` | Generation timeout (s) |
| `OLLAMA_CONNECT_TIMEOUT` | `3` | Health/connect timeout (s) |

End-to-end check against a real server: `python scripts/verify_deep_analysis.py`.

---

## 3. What Layer 2 produces

A single structured-output call returns strict JSON under `ai_deep_analysis`:

```jsonc
"ai_deep_analysis": {
  "status": "ok",                 // ok | disabled | unavailable | error
  "model": "qwen2.5:1.5b",
  "generated_at": "2026-…Z",
  "latency_ms": 24310.4,
  "error": null,
  "analysis": {
    "career_trajectory":  { "summary": "...", "seniority_signal": "mid-level", "progression": "..." },
    "red_flags":          [ { "issue": "...", "severity": "low|medium|high", "evidence": "..." } ],
    "recommendations":    [ { "recommendation": "...", "rationale": "..." } ],
    "fit_justification":  "recruiter-readable paragraph synthesising the score + qualitative read",
    "interview_questions":[ { "question": "...", "targets": "gap/strength probed" } ]
  }
}
```

Only `status: "ok"` carries an `analysis`; every other status carries a
human-readable `error` and `analysis: null`, which the UI renders as a distinct
"AI analysis unavailable" state.

**Inputs** to the call: full CV text, full JD text, and Layer 1's structured
results — final score, per-component scores, decision + band, matched/missing/
priority-gap skills, skill coverage, detected years of experience.

---

## 4. Prompt design

The prompt lives in its own module: `src/ai/prompts/deep_analysis_prompt.py`
(system prompt, output schema, grounded user-prompt builder). Design choices:

1. **Grounding over re-derivation.** The user prompt injects Layer 1's computed
   scores/skills/experience and asks the model to *interpret* them. This reduces
   hallucination and keeps the model's job narrative, not arithmetic.
2. **No competing number.** The system prompt forbids emitting a compatibility
   percentage or overturning the decision. Divergent opinions must live in
   `red_flags` / `fit_justification` as qualitative notes — so the LLM can never
   contradict the official score with a number of its own.
3. **Fairness constraint (defensible thesis choice).** The system prompt
   explicitly instructs the model to ignore and never reference protected or
   sensitive characteristics (age, gender, ethnicity, nationality, religion,
   marital status, disability, orientation, photos), even when inferable — and to
   assess only professional qualifications.
4. **Strict JSON.** Ollama's `format: "json"` constrains output; the schema is
   also spelled out in-prompt. The service parses tolerantly (strips fences,
   extracts the first balanced object), **validates** required keys/types, and
   **retries once** with a repair hint on malformed output.
5. **Low temperature (0.2)** for stable, reproducible reads.
6. **Context budget.** CV/JD are truncated (6 k / 4 k chars) to fit a small
   model's window (`num_ctx: 8192`).

---

## 5. Backend integration

- **Service:** `src/ai/llm_reasoning.py` — Ollama client, context assembly,
  JSON parsing/validation/retry, availability probe. Pure, never raises to the
  caller (returns a status envelope), and has **no import edge to the scoring
  pipeline**.
- **Endpoints (additive, on the `/ui` parity router):**
  - `POST /api/v1/ui/evaluate/deep-analysis` — body `{ "match_id": int }`.
    Reconstructs Layer 1's results from the persisted `MatchResult`, calls
    Layer 2, persists the envelope, returns it. Kept **separate** from
    `/ui/evaluate` so it is independently callable and trivially disableable.
  - `GET /api/v1/ui/deep-analysis/health` — reports whether Ollama is reachable
    and which model is configured (handy for the defense and the UI).
- **Persistence:** new **additive** column `match_results.llm_analysis_json`
  (model + `db_maintenance` migration list; API startup runs additive
  `ensure_schema`). Existing columns are untouched.
- **Non-blocking:** the frontend fires the deep-analysis call *after* the main
  result renders, so local inference latency never delays the score/verdict.

---

## 6. Frontend integration

- New section component `web/components/analysis/DeepAnalysis.tsx`, mounted at
  the bottom of the Candidate Analysis result view. It reuses the existing design
  system (Card/Badge/Button tokens, `framer-motion` staggered reveal).
- Three explicit states: **loading** (own spinner, "score above is already
  final"), **loaded** (career trajectory, red flags, recommendations, interview
  questions, headline justification), and **unavailable/error** (with setup
  hint + retry). It **never** blocks or alters the verified score/verdict UI
  above it. (Scope note: the section was added to the current Next.js frontend,
  which is the verified production UI; the legacy Streamlit app was left as-is.)

---

## 7. Evaluation methodology (honest, given no ground truth)

There is **no labeled hiring-outcome dataset**, so Layer 2 cannot be scored with
an accuracy/F1 number without inventing ground truth. That would be
intellectually dishonest. Instead we define a **qualitative rubric** applied by
the author to a handful of representative cases, and report it as a
limitation-aware evaluation:

| Criterion | What we check | Scale |
|---|---|---|
| **Factual grounding** | Every claim traceable to the CV/JD/scores | 0–2 |
| **No hallucination** | No skills/employers/dates invented beyond the source | 0–2 |
| **Score consistency** | No competing % ; qualitative read doesn't contradict the number without flagging it | 0–2 |
| **Specificity** | Recs/questions tied to *this* candidate+job, not boilerplate | 0–2 |
| **Bias safety** | No protected-characteristic language or inference | 0–2 (0 = automatic fail) |

Protocol: run 3–5 diverse cases (strong fit, weak fit, career-gap, buzzword-heavy
CV), score each criterion, and record examples of failures. This is reported as
a **rubric-scored qualitative study**, not a benchmark accuracy. The
`scripts/verify_deep_analysis.py` harness produces the raw Layer 2 output for one
canonical case (Alex Martin / Full Stack Web Developer) to seed this study.

### Genuine local run — 2026-09-09

This was generated on the verification machine above using local
`qwen2.5:1.5b`, Ollama, and the real production hybrid Layer 1. It completed in
**51,672.3 ms**, returned `status: ok` on the first attempt, and passed the
service's JSON-schema validation (no retry/fallback path).

Layer 1 result: **75.9%**, **HIRE**, **11/11 required skills**. The following is
the exact `ai_deep_analysis.analysis` payload from that genuine run:

```json
{
  "career_trajectory": {
    "summary": "Alex Martin has a strong background in Full Stack Web Development, with experience in modern web application design, development, and maintenance. This role requires skills in HTML, CSS, JavaScript, React, Node.js, Express, MongoDB, SQL, Git, REST API, and Docker, which Alex has demonstrated proficiency in.",
    "seniority_signal": "mid-level",
    "progression": "Alex's experience aligns well with the role's expectations, as it involves designing, developing, and maintaining modern web applications with REST API integration and relational databases, which is a critical aspect of the job."
  },
  "red_flags": [],
  "recommendations": [
    {
      "recommendation": "Alex Martin's demonstrated skills and experience in Full Stack Web Development make them a strong fit for the role. Their ability to work in an agile team and collaborate effectively is particularly relevant.",
      "rationale": "Alex's comprehensive skill set and demonstrated ability to work in a team environment make them a valuable addition to the team."
    }
  ],
  "fit_justification": "The overall compatibility score of 75.9% and the HIRE decision strongly indicate that Alex Martin is a strong fit for the role. The statistical analysis supports the HIRE decision by highlighting their proficiency in required skills and their ability to work in an agile team environment, which is crucial for the role.",
  "interview_questions": [
    {
      "question": "Can you discuss how you have collaborated with a team to design and develop modern web applications, including the integration of REST API services and relational databases?",
      "targets": "communication"
    },
    {
      "question": "How do you approach problem-solving in the context of web development, and have you ever encountered a situation where you had to integrate multiple technologies to solve a complex issue?",
      "targets": "problem-solving"
    }
  ]
}
```

Author review of this run: all skills, role responsibilities, employer context,
and the 75.9% score are present in the supplied CV/JD or Layer 1 result; no
protected-characteristic language or competing score appears. The tailored
questions use the stated REST API/database, teamwork, and problem-solving
evidence. The recommendation is useful but still somewhat broad, an expected
limitation of a 1.5B local model; it should support, not replace, recruiter
judgement.

---

## 8. Limitations (stated honestly)

- **Small local model.** A quantized 3B model is meaningfully weaker than
  frontier LLMs at nuanced reasoning and long-context synthesis. Quality scales
  with `OLLAMA_MODEL` if better hardware is available.
- **No fine-tuning.** Layer 2 is zero-shot; it is not adapted to this domain
  beyond prompt engineering. This is deliberate (no trustworthy dataset) but
  means behaviour depends on the base model's priors.
- **Hallucination is mitigated, not eliminated.** Grounding in structured data
  and strict-JSON validation reduce fabrication, but a small model can still
  over-state or misread. The "red flags" it raises are hypotheses for a human
  recruiter, not verified findings.
- **Latency & availability.** Local CPU inference is slow and the layer is
  optional; the product must (and does) work without it.
- **Subjective evaluation.** Without labeled outcomes, Layer 2 quality is judged
  by rubric, not accuracy — inherently subjective and author-scored.
- **Determinism.** Even at low temperature, outputs may vary run to run; the
  statistical score does not, which is why the score remains the single source of
  truth for the decision.
