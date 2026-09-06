"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  Briefcase, Clock, Download, FileText, Lightbulb, RotateCcw, Target,
  TrendingUp, Upload, Code2, Brain, Share2, List,
} from "lucide-react";
import { api } from "@/lib/api/client";
import type { EvaluatePayload, JobOffer, ModelKey } from "@/lib/api/types";
import { useToast } from "@/components/ui/Toast";
import { useDecisionConfig } from "@/lib/decision-config";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Input, Select, Textarea, Label } from "@/components/ui/Field";
import { RadarChart } from "@/components/ui/RadarChart";
import { ScoreReveal } from "@/components/score/ScoreReveal";
import { ScoreBreakdown } from "@/components/score/ScoreBreakdown";
import { SkillChipGroup } from "@/components/skills/SkillChips";
import { SkillConstellation } from "@/components/skills/SkillConstellation";
import { PageHeader } from "@/components/layout/PageHeader";
import { DeepAnalysis } from "@/components/analysis/DeepAnalysis";
import { MODEL_OPTIONS } from "@/lib/constants";
import { staggerContainer, fadeUp } from "@/lib/motion";
import { cn } from "@/lib/utils";

const SAMPLE_CV = `PROFILE
Senior ML Engineer with 6 years of experience building production AI systems.

SKILLS
Python, PyTorch, TensorFlow, MLflow, Docker, Kubernetes, FastAPI, PostgreSQL, AWS, CI/CD, strong communication and teamwork skills.

EXPERIENCE
2018–2024: ML Engineer at TechCorp. Built and maintained production ML pipelines serving 10M users daily. Led a team of 4 engineers.

EDUCATION
MSc Computer Science — University of Paris`;

type Phase = "form" | "working" | "result";
type Source = "paste" | "upload";

export default function AnalysisPage() {
  const toast = useToast();
  const cfg = useDecisionConfig();
  const [jobs, setJobs] = useState<JobOffer[]>([]);
  const [jobId, setJobId] = useState<number | null>(null);
  const [model, setModel] = useState<ModelKey>("hybrid");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [source, setSource] = useState<Source>("paste");
  const [cv, setCv] = useState(SAMPLE_CV);
  const [file, setFile] = useState<File | null>(null);
  const [phase, setPhase] = useState<Phase>("form");
  const [result, setResult] = useState<EvaluatePayload | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.jobOffers().then((all) => {
      const active = all.filter((j) => j.status === "OPEN" || j.status === "ON_HOLD");
      setJobs(active);
      if (active.length) setJobId(active[0].id);
    }).catch(() => setJobs([]));
  }, []);

  const job = jobs.find((j) => j.id === jobId);

  const run = async () => {
    if (!jobId) return toast("error", "Please select a Job Offer.");
    if (source === "paste" && cv.trim().split(/\s+/).length < 5)
      return toast("error", "Please provide more detailed CV text (minimum 5 words).");
    if (source === "upload" && !file) return toast("error", "Please upload a CV file.");

    setPhase("working");
    try {
      let res: EvaluatePayload;
      if (source === "upload" && file) {
        const form = new FormData();
        form.append("cv_file", file);
        form.append("job_offer_id", String(jobId));
        form.append("model", model);
        if (name) form.append("candidate_name", name);
        if (email) form.append("candidate_email", email);
        form.append("strong_fit_threshold", String(cfg.strong));
        form.append("potential_fit_threshold", String(cfg.potential));
        res = await api.evaluateFile(form);
      } else {
        res = await api.evaluate({
          cv_text: cv, job_offer_id: jobId, model,
          candidate_name: name || undefined, candidate_email: email || undefined,
          strong_fit_threshold: cfg.strong, potential_fit_threshold: cfg.potential,
        });
      }
      setResult(res);
      setPhase("result");
    } catch (err) {
      toast("error", err instanceof Error ? err.message : "Evaluation failed.");
      setPhase("form");
    }
  };

  const reset = () => { setResult(null); setFile(null); setPhase("form"); };

  return (
    <div className="flex flex-col gap-6">
      {phase !== "result" ? (
          <motion.div key="form" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col gap-6">
            <PageHeader
              badge="Candidate Evaluation"
              title="Candidate"
              highlight="Analysis"
              subtitle="Evaluate a candidate's profile against a job description using the NeuralHire AI engine — receive a compatibility score, skill breakdown, and a clear hire recommendation."
            />

            <div className="grid gap-4 lg:grid-cols-[1fr_1.4fr]">
              <div className="flex flex-col gap-4">
                <Card elevation={2}>
                  <CardBody className="flex flex-col gap-4">
                    <label className="block">
                      <Label>Target role *</Label>
                      <Select value={jobId ?? ""} onChange={(e) => setJobId(Number(e.target.value))}>
                        {jobs.length === 0 && <option value="">— No open positions —</option>}
                        {jobs.map((j) => (
                          <option key={j.id} value={j.id}>[{j.job_code}] {j.title}</option>
                        ))}
                      </Select>
                    </label>
                    <label className="block">
                      <Label>Evaluation method</Label>
                      <Select value={model} onChange={(e) => setModel(e.target.value as ModelKey)}>
                        {(Object.keys(MODEL_OPTIONS) as ModelKey[]).map((k) => (
                          <option key={k} value={k}>{MODEL_OPTIONS[k]}</option>
                        ))}
                      </Select>
                    </label>
                    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                      <label className="block"><Label>Candidate name</Label>
                        <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Alice Martin" /></label>
                      <label className="block"><Label>Candidate email</Label>
                        <Input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="alice@example.com" /></label>
                    </div>
                    {job && (
                      <div className="rounded-lg bg-surface-raised/60 p-3 text-caption text-ink-secondary">
                        <span className="font-medium">Required: </span>{job.required_skills_raw || "—"}
                      </div>
                    )}
                    <div className="rounded-lg bg-accent/8 px-3 py-2 text-caption text-ink-secondary ring-1 ring-accent/15">
                      Active policy — Strong Fit ≥ {cfg.strong}%, Potential Fit {cfg.potential}–{cfg.strong - 1}%.
                    </div>
                  </CardBody>
                </Card>

                <Button size="lg" onClick={run} disabled={phase === "working"} icon={<Target className="h-4 w-4" />}>
                  Run Evaluation
                </Button>
              </div>

              <Card elevation={2}>
                <CardHeader>
                  <CardTitle>Candidate CV</CardTitle>
                  <div className="flex gap-1 rounded-lg bg-surface-overlay p-0.5">
                    <SourceTab active={source === "paste"} onClick={() => setSource("paste")} icon={<Code2 className="h-3.5 w-3.5" />} label="Paste" />
                    <SourceTab active={source === "upload"} onClick={() => setSource("upload")} icon={<Upload className="h-3.5 w-3.5" />} label="Upload" />
                  </div>
                </CardHeader>
                <CardBody>
                  {source === "paste" ? (
                    <Textarea value={cv} onChange={(e) => setCv(e.target.value)} rows={14}
                      className="font-mono text-caption" placeholder="Paste the candidate's CV text here…" />
                  ) : (
                    <button
                      onClick={() => fileRef.current?.click()}
                      className="flex h-[336px] w-full flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed border-subtle/25 bg-surface-raised/40 text-ink-secondary transition-colors hover:border-accent/50 hover:bg-surface-raised/70"
                    >
                      <Upload className="h-8 w-8 text-ink-muted" />
                      <div className="text-body font-medium text-ink">{file ? file.name : "Drag & drop or click to upload"}</div>
                      <div className="text-caption text-ink-muted">PDF or DOCX</div>
                      <input ref={fileRef} type="file" accept=".pdf,.docx" className="hidden"
                        onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
                    </button>
                  )}
                </CardBody>
              </Card>
            </div>

            {phase === "working" && <WorkingState />}
          </motion.div>
        ) : result ? (
          <ResultView key="result" result={result} name={name} jobTitle={result.job_title} onReset={reset} toast={toast} />
        ) : null}
    </div>
  );
}

function SourceTab({ active, onClick, icon, label }: { active: boolean; onClick: () => void; icon: React.ReactNode; label: string }) {
  return (
    <button onClick={onClick}
      className={cn("flex items-center gap-1.5 rounded-md px-2.5 py-1 text-caption font-medium transition-colors",
        active ? "bg-surface text-ink shadow-e1" : "text-ink-muted hover:text-ink-secondary")}>
      {icon}{label}
    </button>
  );
}

function WorkingState() {
  const steps = ["Parsing CV", "Extracting skills", "Computing semantic match", "Fusing signals", "Reaching a verdict"];
  return (
    <Card elevation={3} className="overflow-hidden">
      <CardBody className="flex flex-col items-center gap-4 py-9">
        <div className="relative h-14 w-14">
          <div className="absolute inset-0 animate-spin rounded-full border-2 border-accent/20 border-t-accent" />
          <div className="absolute inset-2 animate-pulse-glow rounded-full bg-accent/20" />
        </div>
        <div className="text-center">
          <div className="font-display text-h4 font-semibold text-ink">Running AI evaluation…</div>
          <div className="mt-1 text-caption text-ink-muted">First run loads the models — this can take a moment.</div>
          <motion.div variants={staggerContainer(0.18)} initial="hidden" animate="show" className="mt-3 flex flex-wrap justify-center gap-2">
            {steps.map((s) => (
              <motion.span key={s} variants={fadeUp} className="rounded-full bg-surface-raised px-3 py-1 text-caption text-ink-secondary">{s}</motion.span>
            ))}
          </motion.div>
        </div>
      </CardBody>
    </Card>
  );
}

function ResultView({ result, name, jobTitle, onReset, toast }: {
  result: EvaluatePayload; name: string; jobTitle: string; onReset: () => void;
  toast: (k: "success" | "error" | "info", m: string) => void;
}) {
  const ex = result.explanation;
  const decision = result.decision.decision;
  const sa = ex.skill_analysis;
  const sem = ex.semantic_analysis;
  const [tab, setTab] = useState<"skills" | "gaps" | "actions" | "raw">("skills");
  const [skillView, setSkillView] = useState<"map" | "list">("map");
  const [pdfLoading, setPdfLoading] = useState(false);
  const displayName = name || "Candidate";

  const exportPdf = async () => {
    setPdfLoading(true);
    try {
      const blob = await api.reportPdf({
        result: result.result, explanation: ex, recommendations: result.recommendations,
        candidate_name: displayName, job_title: jobTitle,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = `NeuralHire_${displayName.replace(/\s+/g, "_")}.pdf`;
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
      toast("success", "Report generated successfully.");
    } catch (err) {
      toast("error", err instanceof Error ? err.message : "PDF generation failed.");
    } finally {
      setPdfLoading(false);
    }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-5">
      {/* summary bar */}
      <Card glass elevation={3} className="sticky top-[76px] z-30 flex flex-col gap-3 p-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded-full bg-[linear-gradient(120deg,#7c5cff,#22cfee)] text-body font-semibold text-white">
            {displayName.slice(0, 1)}
          </div>
          <div>
            <div className="font-display text-h4 font-semibold text-ink">{displayName}</div>
            <div className="flex flex-wrap items-center gap-3 text-caption text-ink-secondary">
              <span className="flex items-center gap-1"><Briefcase className="h-3 w-3" /> {jobTitle}</span>
              <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> {result.processing_time.toFixed(0)} ms</span>
              <span className="flex items-center gap-1"><Target className="h-3 w-3" /> {sa.skill_coverage}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" loading={pdfLoading} icon={<Download className="h-3.5 w-3.5" />} onClick={exportPdf}>Export PDF</Button>
          <Button variant="ghost" size="sm" icon={<RotateCcw className="h-3.5 w-3.5" />} onClick={onReset}>New evaluation</Button>
        </div>
      </Card>

      {/* score + radar */}
      <div className="grid gap-5 lg:grid-cols-[1fr_1fr]">
        <Card elevation={3} className="relative overflow-hidden">
          <div className={cn("pointer-events-none absolute inset-x-0 top-0 h-40 opacity-60 blur-3xl",
            decision === "HIRE" ? "bg-success/25" : decision === "CONSIDER" ? "bg-warning/25" : "bg-danger/25")} />
          <CardBody className="relative flex flex-col items-center gap-4 py-8">
            <ScoreReveal
              percentage={result.result.percentage}
              decision={decision}
              confidence={result.decision.confidence}
              confidenceLevel={result.decision.confidence_level}
            />
            <p className="mt-2 max-w-md text-center text-body text-ink-secondary">{ex.hiring_recommendation.justification}</p>
          </CardBody>
        </Card>

        <Card elevation={3}>
          <CardHeader><CardTitle>Competency profile</CardTitle><Badge status="accent" dot>vs required</Badge></CardHeader>
          <CardBody className="grid place-items-center">
            {ex.verdict && (
              <div className="mb-2 w-full rounded-lg border border-subtle/12 bg-surface-raised/60 px-4 py-2.5 text-center text-caption text-ink-secondary">
                {ex.verdict}
              </div>
            )}
            <RadarChart labels={ex.radar_data.labels} series={[
              { name: "Candidate", values: ex.radar_data.cv_scores, color: "#7c5cff" },
              { name: "Required", values: ex.radar_data.job_requirements, color: "#22cfee", dashed: true },
            ]} />
          </CardBody>
        </Card>
      </div>

      {/* breakdown + experience */}
      <div className="grid gap-5 lg:grid-cols-[1.4fr_1fr]">
        <Card elevation={2}><CardHeader><CardTitle>Score breakdown</CardTitle></CardHeader>
          <CardBody><ScoreBreakdown scores={result.result.component_scores} /></CardBody></Card>
        <Card elevation={2}><CardHeader><CardTitle>Experience fit</CardTitle></CardHeader>
          <CardBody className="flex flex-col gap-3 text-body">
            <Row label="Experience" value={`${ex.experience_fit.candidate_years} yrs`} sub={`~${ex.experience_fit.estimated_required_years} required`} />
            <Row label="Status" value={ex.experience_fit.fit_status} tone={ex.experience_fit.fit_status.includes("Below") ? "danger" : "success"} />
            <Row label="Education" value={ex.experience_fit.education_level} />
            <Row label="Semantic alignment" value={sem.interpretation} />
          </CardBody></Card>
      </div>

      {/* tabbed analysis (Skills / Strengths & Gaps / Recommended Actions / Raw) */}
      <Card elevation={2}>
        <CardHeader className="flex-wrap gap-2">
          <div className="flex gap-1 rounded-lg bg-surface-overlay p-0.5">
            {([["skills", "Skills Match"], ["gaps", "Strengths & Gaps"], ["actions", "Recommended Actions"], ["raw", "Raw Data"]] as const).map(([k, l]) => (
              <button key={k} onClick={() => setTab(k)}
                className={cn("rounded-md px-3 py-1.5 text-caption font-medium transition-colors",
                  tab === k ? "bg-surface text-ink shadow-e1" : "text-ink-muted hover:text-ink-secondary")}>{l}</button>
            ))}
          </div>
        </CardHeader>
        <CardBody>
          {tab === "skills" && (
            <div className="flex flex-col gap-5">
              <div className="flex items-center justify-between">
                <span className="text-caption text-ink-secondary">Skill coverage · {sa.skill_coverage}</span>
                <div className="flex gap-1 rounded-lg bg-surface-overlay p-0.5">
                  <button
                    onClick={() => setSkillView("map")}
                    className={cn("flex items-center gap-1.5 rounded-md px-2.5 py-1 text-caption font-medium transition-colors",
                      skillView === "map" ? "bg-surface text-ink shadow-e1" : "text-ink-muted hover:text-ink-secondary")}
                  >
                    <Share2 className="h-3.5 w-3.5" /> Constellation
                  </button>
                  <button
                    onClick={() => setSkillView("list")}
                    className={cn("flex items-center gap-1.5 rounded-md px-2.5 py-1 text-caption font-medium transition-colors",
                      skillView === "list" ? "bg-surface text-ink shadow-e1" : "text-ink-muted hover:text-ink-secondary")}
                  >
                    <List className="h-3.5 w-3.5" /> List
                  </button>
                </div>
              </div>
              {skillView === "map" ? (
                <div className="grid place-items-center py-2">
                  <SkillConstellation
                    matched={sa.matching_skills}
                    priority={sa.critical_missing}
                    missing={sa.missing_skills}
                    extra={sa.extra_skills}
                  />
                </div>
              ) : (
                <div className="grid gap-5 sm:grid-cols-2">
                  <SkillChipGroup group="matched" skills={sa.matching_skills} />
                  <SkillChipGroup group="priority" skills={sa.critical_missing} />
                  <SkillChipGroup group="missing" skills={sa.missing_skills} />
                  <SkillChipGroup group="extra" skills={sa.extra_skills} />
                </div>
              )}
              <div className="grid grid-cols-3 gap-3 border-t border-subtle/10 pt-4">
                <Metric icon={<Brain className="h-4 w-4" />} label="Semantic Match" value={`${sem.score.toFixed(1)}%`} />
                <Metric label="Topic Overlap" value={`${(sem.theme_overlap * 100).toFixed(0)}%`} />
                <Metric label="Interpretation" value={sem.interpretation} small />
              </div>
            </div>
          )}
          {tab === "gaps" && (
            <div className="grid gap-5 lg:grid-cols-3">
              <ListCard title="Strengths" tone="success" items={ex.gap_analysis.strengths} />
              <ListCard title="Blocking gaps" tone="danger" items={ex.gap_analysis.blocking_gaps.length ? ex.gap_analysis.blocking_gaps : ["No blocking gaps detected"]} />
              <ListCard title="Minor gaps" tone="warning" items={ex.gap_analysis.minor_gaps.length ? ex.gap_analysis.minor_gaps : ["None"]} />
            </div>
          )}
          {tab === "actions" && (
            <div className="grid gap-5 md:grid-cols-2">
              <div>
                <div className="mb-2 text-caption font-medium text-ink-secondary">Priority actions</div>
                <div className="flex flex-col gap-2">
                  {result.recommendations.priority_actions.length === 0 && <div className="text-body text-ink-muted">No priority actions — strong coverage.</div>}
                  {result.recommendations.priority_actions.map((a) => (
                    <a key={a.skill} href={a.resource} target="_blank" rel="noreferrer"
                      className="flex items-center justify-between rounded-lg border border-subtle/12 bg-surface-raised/60 px-3 py-2.5 transition-colors hover:border-accent/30">
                      <span className="flex items-center gap-2">
                        <Badge status={a.importance === "critical" ? "danger" : "warning"}>{a.importance}</Badge>
                        <span className="font-medium text-ink">{a.skill}</span>
                      </span>
                      <span className="text-caption text-accent-300">Learn →</span>
                    </a>
                  ))}
                </div>
              </div>
              <div className="flex flex-col gap-3">
                <div className="flex items-center gap-3 rounded-lg bg-accent/8 p-4 ring-1 ring-accent/15">
                  <TrendingUp className="h-5 w-5 text-accent-300" />
                  <div><div className="text-caption text-ink-secondary">Match potential</div>
                    <div className="font-medium text-ink">{result.recommendations.match_potential}</div></div>
                </div>
                <div className="flex items-center gap-3 rounded-lg bg-surface-raised/60 p-4">
                  <Clock className="h-5 w-5 text-ink-muted" />
                  <div><div className="text-caption text-ink-secondary">Estimated ramp-up</div>
                    <div className="font-medium text-ink">{result.recommendations.learning_time_estimate}</div></div>
                </div>
                <div><div className="mb-2 text-caption font-medium text-ink-secondary">Keywords to add</div>
                  <div className="flex flex-wrap gap-2">
                    {result.recommendations.keywords_to_add.map((k) => (
                      <span key={k} className="rounded-full bg-surface-overlay px-2.5 py-1 text-caption text-ink-secondary">{k}</span>
                    ))}
                  </div>
                </div>
                <div className="rounded-lg border border-subtle/10 p-4">
                  <div className="mb-2 text-caption font-medium text-ink-secondary">CV improvements</div>
                  <ul className="flex flex-col gap-1.5 text-body text-ink-secondary">
                    {result.recommendations.cv_improvements.map((c, i) => (
                      <li key={i} className="flex gap-2"><span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent-400" />{c}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
          {tab === "raw" && (
            <pre className="max-h-[420px] overflow-auto rounded-lg bg-surface-raised/60 p-4 font-mono text-caption text-ink-secondary">
              {JSON.stringify(result, null, 2)}
            </pre>
          )}
        </CardBody>
      </Card>

      {/* AI Deep Analysis (Layer 2) — loads after the statistical result above */}
      <DeepAnalysis matchId={result.match_id} />

      <div className="flex items-center gap-2 text-caption text-ink-muted">
        <Lightbulb className="h-3.5 w-3.5" />
        Decision policy at evaluation time — Strong Fit ≥ {result.decision.strong_fit_threshold}%, Potential Fit ≥ {result.decision.potential_fit_threshold}%.
      </div>
    </motion.div>
  );
}

function Row({ label, value, sub, tone }: { label: string; value: string; sub?: string; tone?: "success" | "danger" }) {
  return (
    <div className="flex items-center justify-between border-b border-subtle/8 pb-2.5 last:border-0">
      <span className="text-ink-secondary">{label}</span>
      <span className="text-right">
        <span className={cn("font-medium", tone === "danger" ? "text-danger-fg" : tone === "success" ? "text-success-fg" : "text-ink")}>{value}</span>
        {sub && <span className="ml-1 text-caption text-ink-muted">{sub}</span>}
      </span>
    </div>
  );
}

function Metric({ icon, label, value, small }: { icon?: React.ReactNode; label: string; value: string; small?: boolean }) {
  return (
    <div className="rounded-lg bg-surface-raised/60 p-3">
      <div className="flex items-center gap-1.5 text-caption text-ink-secondary">{icon}{label}</div>
      <div className={cn("mt-1 font-semibold text-ink", small ? "text-body" : "font-display text-h3")}>{value}</div>
    </div>
  );
}

function ListCard({ title, tone, items }: { title: string; tone: "success" | "danger" | "warning"; items: string[] }) {
  const dot = tone === "success" ? "bg-success" : tone === "danger" ? "bg-danger" : "bg-warning";
  return (
    <div className="rounded-lg border border-subtle/12 bg-surface-raised/40 p-4">
      <div className="mb-2.5 font-display text-h4 font-semibold text-ink">{title}</div>
      <ul className="flex flex-col gap-2.5">
        {items.map((it, i) => (
          <li key={i} className="flex gap-2.5 text-body text-ink-secondary">
            <span className={cn("mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full", dot)} />{it}
          </li>
        ))}
      </ul>
    </div>
  );
}
