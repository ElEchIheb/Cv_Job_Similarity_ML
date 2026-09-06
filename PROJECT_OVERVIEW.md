# NeuralHire — Executive Summary

NeuralHire is an enterprise-grade AI Recruitment and Talent Intelligence Platform designed to automate the screening, analysis, and ranking of candidates by matching CVs against Job Descriptions. By utilizing a hybrid NLP scoring engine, NeuralHire removes the subjectivity of manual screening, accelerates the recruitment pipeline, and provides HR professionals with actionable, explainable insights.

## Core Value Proposition

- **Accelerated Screening**: Reduces the time-to-hire by automating CV parsing and matching.
- **Explainable Decisions**: Generates clear, structured justifications for candidate evaluations, outlining skill coverages, gaps, and training actions.
- **Stateless & GDPR-Compliant**: Architected as a lightweight stateless API that processes data in-memory without persistent databases, mitigating risks associated with candidate data storage.
- **Enterprise SaaS Design**: A refined, dark glassmorphism web interface powered by Streamlit that mirrors modern industrial hiring tools.

## Key Features

1. **Executive Recruitment Dashboard**: Displays real-time usage metrics, processing throughput, and system health status.
2. **Interactive Candidate Analysis**: Allows recruiters to upload PDF/DOCX resumes, run multi-model evaluations, visualize skill radars, and download PDF reports.
3. **Talent Leaderboard**: Enables bulk-uploading of candidates to rank them against a single job description, sorting them by suitability.
4. **Explainability Engine**: Provides hiring verdicts ("HIRE", "CONSIDER", "REJECT") with confidence metrics and customized learning action plans.

## High-Level Architecture

```
[ Recruiter Web App ] ── HTTP/REST ──> [ FastAPI Backend ]
                                               │
                       ┌───────────────────────┴───────────────────────┐
                       ▼                                               ▼
             [ Parsing & Preprocessing ]                      [ Hybrid Matching Engine ]
            - pdfplumber (Two-column)                        - TF-IDF Vectorizer
            - python-docx & XML Fallbacks                    - SentenceTransformers (all-MiniLM-L6-v2)
            - Lemmatization & Stopwords                      - Skill & Domain Overlap Matcher
```

---
*For a deep technical dive into the algorithms, API schemas, and testing pipelines, refer to [TECHNICAL_DOCUMENTATION.md](file:///d:/education/pfe/pfe_ai/TECHNICAL_DOCUMENTATION.md).*
