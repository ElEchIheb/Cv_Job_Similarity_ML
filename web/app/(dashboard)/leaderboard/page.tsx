"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Award, CheckCircle2, Download, MinusCircle, Trophy, Upload, Users, X, XCircle } from "lucide-react";
import { api } from "@/lib/api/client";
import type { Decision, JobOffer } from "@/lib/api/types";
import { useDecisionConfig } from "@/lib/decision-config";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Pill } from "@/components/ui/Pill";
import { Select, Label } from "@/components/ui/Field";
import { EmptyState } from "@/components/ui/DataStates";
import { useToast } from "@/components/ui/Toast";
import { BAND_LABEL, DECISION_STATUS } from "@/lib/constants";
import { cn } from "@/lib/utils";

interface Ranked {
  name: string;
  score: number; // pct
  decision: Decision | "ERROR";
  confidence: string;
  matched: string[];
  critical: string[];
  summary: string;
}

const nameFromFile = (fn: string) =>
  fn.replace(/\.[^.]+$/, "").replace(/[_-]+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()).trim();

export default function LeaderboardPage() {
  const toast = useToast();
  const cfg = useDecisionConfig();
  const [jobs, setJobs] = useState<JobOffer[]>([]);
  const [jobId, setJobId] = useState<number | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<Ranked[] | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.jobOffers().then((all) => {
      const active = all.filter((j) => j.status === "OPEN" || j.status === "ON_HOLD");
      setJobs(active);
      if (active.length) setJobId(active[0].id);
    }).catch(() => {});
  }, []);

  const addFiles = (list: FileList | null) => {
    if (!list) return;
    const ok = Array.from(list).filter((f) => /\.(pdf|docx)$/i.test(f.name));
    setFiles((prev) => [...prev, ...ok]);
  };

  const rank = async () => {
    if (!jobId) return toast("error", "Please select a job offer before ranking.");
    if (!files.length) return toast("error", "Please upload at least one CV.");
    setRunning(true);
    setProgress(0);
    setResults(null);
    const out: Ranked[] = [];
    for (let i = 0; i < files.length; i++) {
      const f = files[i];
      setProgress(Math.round(((i + 1) / files.length) * 100));
      const name = nameFromFile(f.name);
      try {
        const form = new FormData();
        form.append("cv_file", f);
        form.append("job_offer_id", String(jobId));
        form.append("model", "hybrid");
        form.append("candidate_name", name);
        form.append("strong_fit_threshold", String(cfg.strong));
        form.append("potential_fit_threshold", String(cfg.potential));
        const r = await api.evaluateFile(form);
        const ex = r.explanation;
        out.push({
          name,
          score: r.result.percentage,
          decision: r.decision.decision,
          confidence: r.decision.confidence_level,
          matched: ex.skill_analysis.matching_skills,
          critical: ex.skill_analysis.critical_missing,
          summary: ex.hiring_recommendation.justification,
        });
      } catch (e) {
        out.push({ name, score: 0, decision: "ERROR", confidence: "", matched: [], critical: [], summary: e instanceof Error ? e.message : "Failed" });
      }
    }
    // sort: score desc, name asc (deterministic ties)
    out.sort((a, b) => b.score - a.score || a.name.toLowerCase().localeCompare(b.name.toLowerCase()));
    setResults(out);
    setRunning(false);
  };

  const valid = (results ?? []).filter((r) => r.decision !== "ERROR");
  const nHire = valid.filter((r) => r.decision === "HIRE").length;
  const nCons = valid.filter((r) => r.decision === "CONSIDER").length;
  const nRej = valid.filter((r) => r.decision === "REJECT").length;
  const avg = valid.length ? valid.reduce((s, r) => s + r.score, 0) / valid.length : 0;
  const top = valid.length ? valid[0].score : 0;

  const exportCsv = () => {
    if (!results) return;
    const header = ["Rank", "Candidate", "Score (%)", "Decision", "Matched Skills", "Priority Gaps"];
    const lines = results.map((r, i) => [
      i + 1, `"${r.name}"`, r.score.toFixed(1), r.decision,
      `"${r.matched.slice(0, 5).join(", ")}"`, `"${r.critical.slice(0, 3).join(", ")}"`,
    ].join(","));
    const csv = [header.join(","), ...lines].join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    const a = document.createElement("a");
    a.href = url; a.download = "neuralhire_ranking.csv"; document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  };

  const maxScore = Math.max(1, ...(results ?? []).map((r) => r.score));

  return (
    <div className="flex flex-col gap-6">
      <PageHeader badge="Talent Leaderboard" title="Talent" highlight="Leaderboard"
        subtitle="Upload multiple CVs and a single job description. NeuralHire ranks every candidate by AI compatibility score with a full skill breakdown and hire decision for each." />

      <div className="grid gap-4 lg:grid-cols-[1fr_1.6fr]">
        <Card elevation={2}>
          <CardHeader><CardTitle className="text-h4">Job description</CardTitle></CardHeader>
          <CardBody>
            <Label>Select Job Offer *</Label>
            <Select value={jobId ?? ""} onChange={(e) => setJobId(Number(e.target.value))}>
              {jobs.length === 0 && <option value="">— No open positions —</option>}
              {jobs.map((j) => <option key={j.id} value={j.id}>[{j.job_code}] {j.title}</option>)}
            </Select>
            <div className="mt-3 rounded-lg bg-accent/8 px-3 py-2 text-caption text-ink-secondary ring-1 ring-accent/15">
              Active policy — Strong Fit ≥ {cfg.strong}%, Potential Fit {cfg.potential}–{cfg.strong - 1}%.
            </div>
          </CardBody>
        </Card>

        <Card elevation={2}>
          <CardHeader><CardTitle className="text-h4">Candidate CVs</CardTitle>
            {files.length > 0 && <Badge status="accent">{files.length} loaded</Badge>}</CardHeader>
          <CardBody>
            <motion.div
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => { e.preventDefault(); setDragOver(false); addFiles(e.dataTransfer.files); }}
              animate={dragOver ? { scale: 1.01 } : { scale: 1 }}
              onClick={() => fileRef.current?.click()}
              className={cn("flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed py-8 transition-colors",
                dragOver ? "border-accent bg-accent/8 animate-border-pulse" : "border-subtle/25 bg-surface-raised/40 hover:border-accent/50")}
            >
              <Upload className="h-7 w-7 text-ink-muted" />
              <div className="text-body font-medium text-ink">Drag & drop CVs, or click to browse</div>
              <div className="text-caption text-ink-muted">Multiple PDF or DOCX files — one per candidate</div>
              <input ref={fileRef} type="file" accept=".pdf,.docx" multiple className="hidden" onChange={(e) => addFiles(e.target.files)} />
            </motion.div>
            {files.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {files.map((f, i) => (
                  <span key={i} className="inline-flex items-center gap-1.5 rounded-full bg-surface-overlay px-2.5 py-1 text-caption text-ink-secondary">
                    {f.name}
                    <button onClick={() => setFiles(files.filter((_, j) => j !== i))} className="text-ink-muted hover:text-danger-fg"><X className="h-3 w-3" /></button>
                  </span>
                ))}
              </div>
            )}
            <Button size="lg" className="mt-4 w-full" loading={running} onClick={rank} icon={<Trophy className="h-4 w-4" />}>
              {running ? `Evaluating… ${progress}%` : "Rank All Candidates"}
            </Button>
            {running && (
              <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-surface-overlay">
                <div className="h-full rounded-full bg-accent transition-all" style={{ width: `${progress}%` }} />
              </div>
            )}
          </CardBody>
        </Card>
      </div>

      {!results && !running && (
        <EmptyState icon={<Users className="h-8 w-8" />} title="No candidates added yet" desc='Upload CVs above, then click "Rank All Candidates" to start the evaluation.' />
      )}

      {results && results.length > 0 && (
        <>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
            <MiniStat icon={<Users className="h-4 w-4" />} label="Candidates" value={results.length} tone="accent" />
            <MiniStat icon={<CheckCircle2 className="h-4 w-4" />} label="Strong Fit" value={nHire} tone="success" />
            <MiniStat icon={<MinusCircle className="h-4 w-4" />} label="Potential Fit" value={nCons} tone="warning" />
            <MiniStat icon={<XCircle className="h-4 w-4" />} label="Low Fit" value={nRej} tone="danger" />
            <MiniStat icon={<Award className="h-4 w-4" />} label="Avg Score" value={`${avg.toFixed(0)}%`} tone="accent" />
            <MiniStat icon={<Trophy className="h-4 w-4" />} label="Top Score" value={`${top.toFixed(0)}%`} tone="cyan" />
          </div>

          <Card elevation={2}>
            <CardHeader><CardTitle className="text-h4">Score distribution</CardTitle>
              <Button variant="secondary" size="sm" icon={<Download className="h-3.5 w-3.5" />} onClick={exportCsv}>Export CSV</Button></CardHeader>
            <CardBody className="flex flex-col gap-2">
              {results.map((r, i) => {
                const tone = r.decision === "ERROR" ? "neutral" : DECISION_STATUS[r.decision];
                return (
                  <div key={i} className="flex items-center gap-3">
                    <span className="w-32 shrink-0 truncate text-caption text-ink-secondary">{r.name}</span>
                    <div className="h-3 flex-1 overflow-hidden rounded-full bg-surface-overlay">
                      <motion.div className={cn("h-full rounded-full", tone === "success" ? "bg-success" : tone === "warning" ? "bg-warning" : tone === "danger" ? "bg-danger" : "bg-ink-muted")}
                        initial={{ width: 0 }} animate={{ width: `${(r.score / maxScore) * 100}%` }} transition={{ duration: 0.7, delay: i * 0.03 }} />
                    </div>
                    <span className="tnum w-10 text-right text-caption font-medium text-ink">{r.score.toFixed(0)}%</span>
                  </div>
                );
              })}
            </CardBody>
          </Card>

          <div className="flex flex-col gap-3">
            {results.map((r, i) => <LeaderCard key={i} rank={i + 1} r={r} />)}
          </div>

          {valid.length > 0 && (
            <Card elevation={2} className={cn("border-l-4",
              valid[0].decision === "HIRE" ? "border-l-success" : valid[0].decision === "CONSIDER" ? "border-l-warning" : "border-l-danger")}>
              <CardBody>
                <div className="mb-1 flex items-center gap-2 text-micro font-semibold uppercase tracking-wide text-ink-muted">
                  <Award className="h-3.5 w-3.5" /> Top candidate · {valid[0].name}
                </div>
                <p className="text-body text-ink-secondary">{valid[0].summary}</p>
              </CardBody>
            </Card>
          )}
        </>
      )}
    </div>
  );
}

function MiniStat({ icon, label, value, tone }: { icon: React.ReactNode; label: string; value: number | string; tone: string }) {
  const t: Record<string, string> = { accent: "text-accent-300 bg-accent/12", success: "text-success-fg bg-success-soft", warning: "text-warning-fg bg-warning-soft", danger: "text-danger-fg bg-danger-soft", cyan: "text-cyan-400 bg-cyan-500/12" };
  return (
    <div className="rounded-lg border border-subtle/12 bg-surface p-4 shadow-e1">
      <span className={cn("mb-2 inline-grid h-8 w-8 place-items-center rounded-lg", t[tone])}>{icon}</span>
      <div className="font-display text-h3 font-semibold text-ink tnum">{value}</div>
      <div className="text-caption text-ink-secondary">{label}</div>
    </div>
  );
}

function LeaderCard({ rank, r }: { rank: number; r: Ranked }) {
  const ref = useRef<HTMLDivElement>(null);
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const onMove = (e: React.MouseEvent) => {
    const el = ref.current; if (!el) return;
    const rect = el.getBoundingClientRect();
    const px = (e.clientX - rect.left) / rect.width - 0.5;
    const py = (e.clientY - rect.top) / rect.height - 0.5;
    setTilt({ x: py * -4, y: px * 4 });
  };
  const err = r.decision === "ERROR";
  const tone = r.decision === "ERROR" ? "neutral" : DECISION_STATUS[r.decision];
  const ring = tone === "success" ? "ring-success/30" : tone === "warning" ? "ring-warning/30" : tone === "danger" ? "ring-danger/30" : "ring-subtle/15";

  return (
    <motion.div
      ref={ref}
      onMouseMove={onMove}
      onMouseLeave={() => setTilt({ x: 0, y: 0 })}
      style={{ transform: `perspective(900px) rotateX(${tilt.x}deg) rotateY(${tilt.y}deg)` }}
      className={cn("rounded-xl border border-subtle/12 bg-surface p-5 shadow-e2 ring-1 transition-shadow hover:shadow-e3", ring)}
    >
      <div className="flex items-center gap-4">
        <div className={cn("grid h-11 w-11 shrink-0 place-items-center rounded-xl font-display text-h4 font-bold",
          rank === 1 ? "bg-[linear-gradient(120deg,#f5b445,#f65cc6)] text-white" : "bg-surface-overlay text-ink-secondary")}>
          {rank}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-display text-h4 font-semibold text-ink">{r.name}</span>
            {r.decision === "ERROR" ? <Badge status="neutral">Error</Badge> : <Badge status={DECISION_STATUS[r.decision]}>{BAND_LABEL[r.decision]}</Badge>}
          </div>
          {!err && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {r.matched.slice(0, 5).map((s) => <Pill key={s} tone="matched">{s}</Pill>)}
              {r.critical.slice(0, 3).map((s) => <Pill key={s} tone="priority">{s}</Pill>)}
            </div>
          )}
          {err && <div className="mt-1 text-caption text-danger-fg">{r.summary}</div>}
        </div>
        <div className="text-right">
          <div className="font-display text-h1 font-bold text-gradient tnum">{r.score.toFixed(0)}%</div>
        </div>
      </div>
    </motion.div>
  );
}
