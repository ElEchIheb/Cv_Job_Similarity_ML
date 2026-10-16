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
  avg_score: number; // 0..1, calibrated results only
  hire_count: number;
  hire_pct: number;
  /** Results scored on the calibrated scale (used for avg_score / hire_pct). */
  current_scale_matches?: number;
  /** Results scored before the calibration (old raw scale, kept as-is). */
  legacy_matches?: number;
}

/** Scale metadata attached to every persisted result. */
export interface ScoreScaleFields {
  score_raw: number | null;
  calibration_version: string | null;
  score_scale: "calibrated" | "legacy";
  legacy_scale: boolean;
  model_version: string | null;
  evaluation_method: string | null;
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
  best_score: number | null; // 0..1, calibrated results only
  legacy_evaluation_count?: number;
}

export interface MatchRow extends Partial<ScoreScaleFields> {
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
  strong_fit_threshold?: number | null;
  potential_fit_threshold?: number | null;
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
  /** Set when HIRE was withheld because the matched skills are weakly evidenced. */
  evidence_gap?: string | null;
  evidence?: {
    copied_tokens: number;
    structure_detected: boolean;
    matched_hard_count: number;
    demonstrated_count: number;
    demonstrated_share: number | null;
    declared_only_skills: string[];
    notes: string[];
  } | null;
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
    /** Calibrated display score (0-100): the thresholds apply to this value. */
    percentage: number;
    final_score: number;
    /** Method's native 0-1 score before calibration. */
    raw_score?: number;
    calibration_version?: string;
    score_scale?: "calibrated" | "uncalibrated";
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
export type DeepAnalysisStatus = "ok" | "disabled" | "unavailable" | "error" | "inconsistent";

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
  /** Calibrated display score (0-100). */
  percentage: number;
  raw_score?: number | null;
  calibration_version?: string | null;
  confidence: string | null;
  speed_ms: number | null;
  decision: Decision | "N/A";
  band_label: string;
  error?: string;
}

export interface MatchDetail extends Partial<ScoreScaleFields> {
  id: number;
  strong_fit_threshold?: number | null;
  potential_fit_threshold?: number | null;
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
// Every value comes from a versioned file under evaluation/results/ (see the
// /ui/quality endpoint). A metric absent from those files is null and must be
// displayed as "not measured", never as zero.
export type VerdictCounts = Record<"REJECT" | "CONSIDER" | "HIRE", number>;
export type QualitySourceStatus =
  | "current" | "stale" | "unversioned" | "missing" | "independent_of_calibration" | "not_measured";
export interface QualitySource {
  key: "verdicts" | "raw" | "robustness" | "fictitious_pdfs" | "personal_trials";
  kind: "synthetic" | "functional" | "personal";
  label: string;
  file: string | null;
  generated: string | null;
  n: number | null;
  unit: string | null;
  calibration_version: string | null;
  status: QualitySourceStatus;
}
export interface VerdictQualityRow {
  key: string;
  label: string;
  role: "shipped" | "comparison" | "before";
  macro_f1: number;
  macro_f1_95ci: [number, number] | null;
  binary_f1: number;
  binary_f1_95ci: [number, number] | null;
  hire_f1: number;
  kappa: number | null;
  verdict_counts: VerdictCounts;
}
export interface RawScoreRow {
  key: string;
  threshold: number | null;
  accuracy: number | null;
  precision: number | null;
  recall: number | null;
  binary_f1: number | null;
  binary_f1_95ci: [number, number] | null;
  roc_auc: number | null;
  pr_auc: number | null;
  inference_ms_per_pair: number | null;
}
export interface Quality {
  available: boolean;
  shipped?: {
    model_version: string;
    calibration_version: string;
    weights: Record<string, number> | null;
    thresholds: { potential_fit: number; strong_fit: number };
    fitted_on: string | null;
    warning: string | null;
  };
  sources?: QualitySource[];
  verdict_quality?: {
    n: number;
    class_support: VerdictCounts;
    rows: VerdictQualityRow[];
    confusion: { verdicts: string[]; classes: string[]; matrix: number[][] };
    per_class: Record<string, { precision: number; recall: number; f1: number; support: number }>;
    paired_hybrid_minus_tfidf: { mean: number; ci95: [number, number]; share_le_0: number } | null;
    subgroups: Record<string, Record<string, { n: number; macro_f1: number }>>;
  } | null;
  raw_score?: {
    n: number | null;
    split_sizes: Record<string, number> | null;
    methodology: string | null;
    rows: RawScoreRow[];
  } | null;
  robustness?: {
    n_per_probe: number | null;
    split: string;
    rows: { key: string; label: string; n: number; base: "unrelated" | "strong"; before: VerdictCounts; after: VerdictCounts }[];
    unrelated_reference: VerdictCounts | null;
    strong_reference: VerdictCounts | null;
    genuine_pairs: { n: number; evidence_cap_rate: number; verdicts_changed: number } | null;
  } | null;
  functional?: {
    n_cvs: number | null;
    verdict_counts: VerdictCounts | null;
    history_consistent: boolean | null;
    pdf_export_ok: boolean;
  } | null;
}
export interface QualityFigure {
  name: string;
  label: string;
  group?: "verdicts" | "ranking";
  stale?: boolean;
  n?: number | null;
}

export interface SystemInfo {
  python_version: string;
  models: { key: ModelKey; label: string; description: string; status: string }[];
  config: { match_threshold: number; embedding_model: string; rate_limit: number };
  defaults: { strong_fit_threshold: number; potential_fit_threshold: number };
  calibration?: {
    version: string;
    calibrated: boolean;
    methods: Record<string, { cut_consider: number; cut_hire: number; ceiling: number }>;
    provenance: Record<string, unknown>;
  };
}
