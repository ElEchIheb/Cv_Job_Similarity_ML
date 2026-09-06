/**
 * Types mirror the live FastAPI contract:
 *   - auth router (src/api/routers/auth.py)
 *   - UI-parity router (src/api/routers/ui.py), which wraps the same in-process
 *     service/DB logic the Streamlit app uses.
 * Keep in sync with the backend; nothing here re-derives business logic.
 */

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
}

export type Decision = "HIRE" | "CONSIDER" | "REJECT";
export type ModelKey = "hybrid" | "embedding" | "tfidf" | "skill";
export type JobStatus = "OPEN" | "ON_HOLD" | "CLOSED";
export type CandidateStatus =
  | "NEW"
  | "UNDER_REVIEW"
  | "SHORTLISTED"
  | "INTERVIEW"
  | "HIRED"
  | "REJECTED";

export interface Overview {
  total_candidates: number;
  total_jobs: number;
  total_matches: number;
  avg_score: number; // 0..1
  hire_count: number;
  hire_pct: number;
}

export interface JobOffer {
  id: number;
  job_code: string | null;
  title: string;
  description: string;
  required_skills_raw: string;
  status: JobStatus;
  created_at: string | null;
  evaluation_count: number;
}

export interface Candidate {
  id: number;
  full_name: string;
  email: string | null;
  phone: string | null;
  status: CandidateStatus;
  is_anonymous: number;
  created_at: string | null;
  evaluation_count: number;
  best_score: number | null; // 0..1
}

export interface MatchRow {
  id: number;
  candidate_id: number | null;
  candidate_name: string;
  candidate_email: string | null;
  job_offer_id: number | null;
  job_title: string;
  job_code: string | null;
  final_score: number | null; // 0..1
  decision: Decision | null;
  confidence: string | null;
  created_at: string | null;
}

export interface ComponentScores {
  hybrid_score?: number;
  embedding_score?: number;
  tfidf_score?: number;
  skill_score?: number;
}

export interface HiringRecommendation {
  decision: Decision;
  band_label: string;
  justification: string;
  confidence: number; // [0,1] uncalibrated
  confidence_level: "high" | "medium" | "low";
}

export interface RadarData {
  labels: string[];
  cv_scores: number[];
  job_requirements: number[];
}

export interface Explanation {
  global_score: number;
  decision_config: { strong_fit_threshold: number; potential_fit_threshold: number };
  verdict: string;
  color: string;
  hiring_recommendation: HiringRecommendation;
  experience_fit: {
    candidate_years: number;
    estimated_required_years: number;
    fit_status: string;
    education_level: string;
  };
  semantic_analysis: {
    score: number;
    interpretation: string;
    key_themes_cv: string[];
    key_themes_job: string[];
    theme_overlap: number;
  };
  skill_analysis: {
    score: number;
    matching_skills: string[];
    missing_skills: string[];
    extra_skills: string[];
    critical_missing: string[];
    skill_coverage: string;
  };
  gap_analysis: {
    blocking_gaps: string[];
    minor_gaps: string[];
    strengths: string[];
  };
  radar_data: RadarData;
}

export interface PriorityAction {
  skill: string;
  importance: "critical" | "important";
  resource: string;
}

export interface Recommendations {
  priority_actions: PriorityAction[];
  cv_improvements: string[];
  keywords_to_add: string[];
  learning_time_estimate: string;
  match_potential: string;
}

export interface DecisionResult {
  decision: Decision;
  band_label: string;
  confidence: number;
  confidence_level: "high" | "medium" | "low";
  reason: string;
  strong_fit_threshold: number;
  potential_fit_threshold: number;
}

/** Full payload from POST /ui/evaluate and /ui/evaluate/file. */
export interface EvaluatePayload {
  result: {
    percentage: number;
    final_score: number;
    component_scores: ComponentScores;
    skill_details?: Record<string, unknown>;
    confidence?: string | null;
  };
  explanation: Explanation;
  recommendations: Recommendations;
  decision: DecisionResult;
  config: { strong_fit_threshold: number; potential_fit_threshold: number };
  model_key: ModelKey;
  match_id: number | null;
  processing_time: number;
  job_title: string;
}

// ── Layer 2: LLM deep analysis (additive) ─────────────────────────────────────
export type DeepAnalysisStatus = "ok" | "disabled" | "unavailable" | "error";

export interface DeepAnalysisContent {
  career_trajectory: { summary: string; seniority_signal: string; progression: string };
  red_flags: { issue: string; severity: string; evidence: string }[];
  recommendations: { recommendation: string; rationale: string }[];
  fit_justification: string;
  interview_questions: { question: string; targets: string }[];
}

export interface DeepAnalysisEnvelope {
  status: DeepAnalysisStatus;
  model: string;
  generated_at: string | null;
  latency_ms: number | null;
  analysis: DeepAnalysisContent | null;
  error: string | null;
}

export interface DeepAnalysisResponse {
  match_id: number;
  ai_deep_analysis: DeepAnalysisEnvelope;
}

export interface CompareRow {
  model: ModelKey;
  percentage: number;
  confidence: string | null;
  speed_ms: number | null;
  decision: Decision | "N/A";
  band_label: string;
  error?: string;
}

export interface MatchDetail {
  id: number;
  candidate_name: string | null;
  job_title: string | null;
  final_score: number | null;
  decision: Decision | null;
  created_at: string | null;
  explanation: Explanation | null;
  recommendations: Recommendations | null;
  raw: Record<string, unknown>;
}

// ── AI Quality Center ────────────────────────────────────────────────────────
export interface QualityMetric {
  accuracy?: number;
  precision?: number;
  recall?: number;
  f1?: number;
  roc_auc?: number;
  inference_ms_per_pair?: number;
}
export interface Quality {
  available: boolean;
  metrics?: Record<string, QualityMetric>;
  analysis?: {
    bootstrap_ci?: Record<string, Record<string, [number, number]>>;
    subgroup_analysis?: {
      seniority_performance?: Record<string, { count: number; auc: number }>;
      domain_performance?: Record<string, { count: number; auc: number }>;
    };
    error_analysis?: {
      fp_count?: number;
      fn_count?: number;
      dominant_fp_domain?: string;
      dominant_fn_domain?: string;
    };
  };
  provenance?: { source: string; generated: string; n_samples?: number | null };
}
export interface QualityFigure {
  name: string;
  label: string;
}

export interface SystemInfo {
  python_version: string;
  models: { key: ModelKey; label: string; description: string; status: string }[];
  config: { match_threshold: number; embedding_model: string; rate_limit: number };
  defaults: { strong_fit_threshold: number; potential_fit_threshold: number };
}
