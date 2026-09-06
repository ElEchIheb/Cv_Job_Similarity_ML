/**
 * NeuralHire API client — talks to the live FastAPI backend only.
 * Auth uses the OAuth2 bearer contract; all data/CRUD/evaluation calls hit the
 * additive /ui parity router which wraps the same logic the Streamlit app runs.
 */
import type {
  Candidate,
  CandidateStatus,
  CompareRow,
  EvaluatePayload,
  JobOffer,
  JobStatus,
  MatchDetail,
  MatchRow,
  ModelKey,
  Overview,
  Quality,
  QualityFigure,
  SystemInfo,
  User,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api/v1";
const TOKEN_KEY = "neuralhire-token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}
export function setToken(t: string | null) {
  try {
    if (t) localStorage.setItem(TOKEN_KEY, t);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage unavailable */
  }
}

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      ...init,
      headers: {
        ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(init?.headers ?? {}),
      },
    });
  } catch {
    throw new ApiError("Cannot reach the NeuralHire backend. Is the API running on :8000?", 0);
  }
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new ApiError((detail as { detail?: string }).detail ?? `Request failed (${res.status})`, res.status);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export interface JobInput {
  title: string;
  description: string;
  required_skills: string;
  status: JobStatus;
}
export interface CandidateInput {
  full_name: string;
  email: string | null;
  phone: string | null;
  status: CandidateStatus;
}
export interface EvaluateInput {
  cv_text: string;
  job_offer_id: number;
  model?: ModelKey;
  candidate_name?: string;
  candidate_email?: string;
  strong_fit_threshold?: number;
  potential_fit_threshold?: number;
}

export const api = {
  // ── auth ────────────────────────────────────────────────────────────────
  async login(email: string, password: string): Promise<{ token: string; user: User }> {
    const body = new URLSearchParams({ username: email, password });
    let res: Response;
    try {
      res = await fetch(`${BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
      });
    } catch {
      throw new ApiError("Cannot reach the backend. Is the API running on :8000?", 0);
    }
    if (!res.ok) {
      const d = await res.json().catch(() => ({}));
      throw new ApiError((d as { detail?: string }).detail ?? "Incorrect email or password", res.status);
    }
    const { access_token } = (await res.json()) as { access_token: string };
    setToken(access_token);
    const user = await req<User>("/auth/me");
    return { token: access_token, user };
  },

  async register(email: string, password: string, full_name: string): Promise<User> {
    return req<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    });
  },

  me: () => req<User>("/auth/me"),
  logout: () => setToken(null),

  // ── overview ────────────────────────────────────────────────────────────
  overview: () => req<Overview>("/ui/overview"),

  // ── job offers ──────────────────────────────────────────────────────────
  jobOffers: () => req<JobOffer[]>("/ui/job-offers"),
  createJob: (body: JobInput) => req<JobOffer>("/ui/job-offers", { method: "POST", body: JSON.stringify(body) }),
  updateJob: (id: number, body: JobInput) =>
    req<JobOffer>(`/ui/job-offers/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  toggleJobStatus: (id: number) => req<JobOffer>(`/ui/job-offers/${id}/toggle-status`, { method: "POST" }),
  deleteJob: (id: number) => req<{ status: string }>(`/ui/job-offers/${id}`, { method: "DELETE" }),

  // ── candidates ──────────────────────────────────────────────────────────
  candidates: () => req<Candidate[]>("/ui/candidates"),
  updateCandidate: (id: number, body: CandidateInput) =>
    req<Candidate>(`/ui/candidates/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteCandidate: (id: number) => req<{ status: string }>(`/ui/candidates/${id}`, { method: "DELETE" }),

  // ── analysis history ────────────────────────────────────────────────────
  matches: () => req<MatchRow[]>("/ui/matches"),
  matchDetail: (id: number) => req<MatchDetail>(`/ui/matches/${id}`),

  // ── evaluation ──────────────────────────────────────────────────────────
  evaluate: (input: EvaluateInput) =>
    req<EvaluatePayload>("/ui/evaluate", { method: "POST", body: JSON.stringify({ model: "hybrid", ...input }) }),
  evaluateFile: (form: FormData) =>
    req<EvaluatePayload>("/ui/evaluate/file", { method: "POST", body: form }),

  // ── ai insights ─────────────────────────────────────────────────────────
  compare: (cv_text: string, job_text: string) =>
    req<{ rows: CompareRow[] }>("/ui/compare", { method: "POST", body: JSON.stringify({ cv_text, job_text }) }),

  // ── quality center ──────────────────────────────────────────────────────
  quality: () => req<Quality>("/ui/quality"),
  qualityFigures: () => req<QualityFigure[]>("/ui/quality/figures"),
  async figureBlob(name: string): Promise<string> {
    const token = getToken();
    const res = await fetch(`${BASE}/ui/quality/figures/${encodeURIComponent(name)}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new ApiError("Figure not found", res.status);
    const blob = await res.blob();
    return URL.createObjectURL(blob);
  },

  // ── settings / system ───────────────────────────────────────────────────
  system: () => req<SystemInfo>("/ui/system"),

  // report PDF (existing endpoint)
  async reportPdf(payload: {
    result: unknown;
    explanation: unknown;
    recommendations: unknown;
    candidate_name?: string;
    job_title?: string;
  }): Promise<Blob> {
    const token = getToken();
    const res = await fetch(`${BASE}/report/pdf`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const d = await res.json().catch(() => ({}));
      throw new ApiError((d as { detail?: string }).detail ?? "PDF generation failed", res.status);
    }
    return res.blob();
  },
};

export { ApiError };
