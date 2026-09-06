/**
 * Display constants ported verbatim from frontend/components/ui.py so the new UI
 * shows exactly the same labels/descriptions as the Streamlit app. These are
 * presentation strings only — no business logic.
 */
import type { Decision, ModelKey } from "./api/types";

export const MODEL_LABELS: Record<ModelKey, string> = {
  hybrid: "Overall AI Match",
  embedding: "Semantic Relevance",
  tfidf: "Keyword Relevance",
  skill: "Skills Assessment",
};

export const MODEL_DESCRIPTIONS: Record<ModelKey, string> = {
  hybrid: "Combines all evaluation dimensions into a single, balanced compatibility score.",
  embedding: "Measures how closely the candidate's experience matches the role at a conceptual level.",
  tfidf: "Analyses keyword alignment between the candidate's profile and job requirements.",
  skill: "Compares detected skills from the CV against the required skills in the job posting.",
};

/** Candidate-Analysis model selector labels (single_match.py _MODEL_OPTIONS). */
export const MODEL_OPTIONS: Record<ModelKey, string> = {
  hybrid: "Overall AI Match — Recommended",
  embedding: "Semantic Relevance only",
  tfidf: "Keyword Relevance only",
  skill: "Skills Assessment only",
};

export const MODEL_COLORS: Record<ModelKey, string> = {
  hybrid: "#F59E0B",
  embedding: "#8B5CF6",
  tfidf: "#6366F1",
  skill: "#06B6D4",
};

/** Component-score key → human label (ui.py SCORE_LABELS). */
export const SCORE_LABELS: Record<string, string> = {
  hybrid_score: "Overall AI Match",
  embedding_score: "Semantic Relevance",
  tfidf_score: "Keyword Relevance",
  skill_score: "Skills Assessment",
};

/** Canonical decision → recruiter band label (decision_engine.BAND_LABELS). */
export const BAND_LABEL: Record<Decision, string> = {
  HIRE: "Strong Fit",
  CONSIDER: "Potential Fit",
  REJECT: "Low Fit",
};

export const DECISION_STATUS: Record<Decision, "success" | "warning" | "danger"> = {
  HIRE: "success",
  CONSIDER: "warning",
  REJECT: "danger",
};

export const JOB_STATUSES = ["OPEN", "ON_HOLD", "CLOSED"] as const;
export const CANDIDATE_STATUSES = [
  "NEW",
  "UNDER_REVIEW",
  "SHORTLISTED",
  "INTERVIEW",
  "HIRED",
  "REJECTED",
] as const;

/** Canonical defaults (decision_engine.DEFAULT_*). */
export const DEFAULT_STRONG_FIT = 75;
export const DEFAULT_POTENTIAL_FIT = 55;

/** Client-side classify — mirrors DecisionEngine.classify for display only.
 *  The authoritative decision always comes from the backend payload; this is
 *  used only for live threshold previews on the Settings page. */
export function classify(pct: number, strong = DEFAULT_STRONG_FIT, potential = DEFAULT_POTENTIAL_FIT): Decision {
  if (pct >= strong) return "HIRE";
  if (pct >= potential) return "CONSIDER";
  return "REJECT";
}
