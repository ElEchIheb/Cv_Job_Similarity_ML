"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Brain, GitCompareArrows, Layers, Search, Zap } from "lucide-react";
import { api } from "@/lib/api/client";
import type { CompareRow, ModelKey } from "@/lib/api/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Textarea, Label } from "@/components/ui/Field";
import { useToast } from "@/components/ui/Toast";
import { MODEL_COLORS, MODEL_DESCRIPTIONS, MODEL_LABELS } from "@/lib/constants";
import { cn } from "@/lib/utils";

const ICONS: Record<ModelKey, React.ReactNode> = {
  hybrid: <Zap className="h-4 w-4" />, embedding: <Brain className="h-4 w-4" />,
  tfidf: <Search className="h-4 w-4" />, skill: <Layers className="h-4 w-4" />,
};

function tier(pct: number) {
  if (pct >= 75) return { label: "Strong Fit", cls: "text-success-fg" };
  if (pct >= 55) return { label: "Potential Fit", cls: "text-warning-fg" };
  return { label: "Low Fit", cls: "text-danger-fg" };
}

export default function InsightsPage() {
  const toast = useToast();
  const [cv, setCv] = useState("");
  const [jd, setJd] = useState("");
  const [rows, setRows] = useState<CompareRow[] | null>(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    if (!cv.trim() || !jd.trim()) return toast("error", "Please provide both a CV and a job description.");
    setLoading(true);
    try {
      const { rows } = await api.compare(cv, jd);
      setRows(rows);
    } catch (e) { toast("error", e instanceof Error ? e.message : "Comparison failed."); }
    finally { setLoading(false); }
  };

  const maxPct = Math.max(1, ...(rows ?? []).map((r) => r.percentage));

  return (
    <div className="flex flex-col gap-6">
      <PageHeader badge="AI Insights & Explainability" title="AI Evaluation" highlight="Insights"
        subtitle="Compare all four evaluation dimensions side-by-side on the same input to understand candidate fit from keyword relevance to deep semantic understanding." />

      <div className="grid gap-4 md:grid-cols-2">
        <Card elevation={2}><CardHeader><CardTitle className="text-h4">Candidate CV</CardTitle></CardHeader>
          <CardBody><Textarea rows={9} value={cv} onChange={(e) => setCv(e.target.value)} placeholder="Paste the candidate's CV here." className="font-mono text-caption" /></CardBody></Card>
        <Card elevation={2}><CardHeader><CardTitle className="text-h4">Job Description</CardTitle></CardHeader>
          <CardBody><Textarea rows={9} value={jd} onChange={(e) => setJd(e.target.value)} placeholder="Paste the job description here." className="font-mono text-caption" /></CardBody></Card>
      </div>

      <div className="flex justify-center">
        <Button size="lg" loading={loading} onClick={run} icon={<GitCompareArrows className="h-4 w-4" />} className="min-w-[280px]">Compare All Methods</Button>
      </div>

      {rows && (
        <>
          <Card elevation={2}><CardHeader><CardTitle className="text-h4">Score comparison</CardTitle></CardHeader>
            <CardBody className="flex flex-col gap-3">
              {rows.map((r) => (
                <div key={r.model} className="flex items-center gap-3">
                  <span className="flex w-40 shrink-0 items-center gap-2 text-caption text-ink-secondary">
                    <span style={{ color: MODEL_COLORS[r.model] }}>{ICONS[r.model]}</span>{MODEL_LABELS[r.model]}
                  </span>
                  <div className="h-3 flex-1 overflow-hidden rounded-full bg-surface-overlay">
                    <motion.div className="h-full rounded-full" style={{ background: MODEL_COLORS[r.model] }}
                      initial={{ width: 0 }} animate={{ width: `${(r.percentage / maxPct) * 100}%` }} transition={{ duration: 0.8 }} />
                  </div>
                  <span className="tnum w-12 text-right text-caption font-medium text-ink">{r.percentage.toFixed(0)}%</span>
                </div>
              ))}
            </CardBody>
          </Card>

          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            {rows.map((r) => {
              const t = tier(r.percentage);
              return (
                <motion.div key={r.model} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                  className="flex flex-col items-center rounded-xl border border-subtle/12 bg-surface p-5 text-center shadow-e2">
                  <span className="mb-3 grid h-10 w-10 place-items-center rounded-lg" style={{ color: MODEL_COLORS[r.model], background: `${MODEL_COLORS[r.model]}1f` }}>{ICONS[r.model]}</span>
                  <div className="text-caption font-semibold text-ink">{MODEL_LABELS[r.model]}</div>
                  <div className="my-1 font-display text-h1 font-bold tnum" style={{ color: MODEL_COLORS[r.model] }}>{r.percentage.toFixed(0)}%</div>
                  <div className={cn("mb-3 text-caption font-semibold", t.cls)}>{t.label}</div>
                  <div className="flex w-full items-center justify-between border-t border-subtle/10 pt-3 text-micro text-ink-muted">
                    <span>Speed: {r.speed_ms != null ? `${r.speed_ms} ms` : "N/A"}</span>
                    <span>Conf: {r.confidence ? String(r.confidence) : "—"}</span>
                  </div>
                </motion.div>
              );
            })}
          </div>

          <Card elevation={1}><CardHeader><CardTitle className="text-h4">Comparison table</CardTitle></CardHeader>
            <CardBody className="overflow-x-auto">
              <table className="w-full min-w-[520px] text-body">
                <thead><tr className="border-b border-subtle/12 text-caption uppercase tracking-wide text-ink-muted">
                  <th className="px-3 py-2 text-left">Evaluation Method</th><th className="px-3 py-2 text-right">Score</th>
                  <th className="px-3 py-2 text-left">Assessment</th><th className="px-3 py-2 text-right">Speed</th><th className="px-3 py-2 text-left">Confidence</th>
                </tr></thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.model} className="border-b border-subtle/8 last:border-0">
                      <td className="px-3 py-2.5 font-medium text-ink">{MODEL_LABELS[r.model]}</td>
                      <td className="px-3 py-2.5 text-right tnum">{r.percentage.toFixed(1)}%</td>
                      <td className={cn("px-3 py-2.5", tier(r.percentage).cls)}>{tier(r.percentage).label}</td>
                      <td className="px-3 py-2.5 text-right tnum text-ink-secondary">{r.speed_ms != null ? `${r.speed_ms} ms` : "N/A"}</td>
                      <td className="px-3 py-2.5 text-ink-secondary">{r.confidence ? String(r.confidence) : "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardBody>
          </Card>
        </>
      )}

      <Card elevation={1}><CardHeader><CardTitle className="text-h4">How each method works</CardTitle></CardHeader>
        <CardBody className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {(Object.keys(MODEL_LABELS) as ModelKey[]).map((k) => (
            <div key={k} className="rounded-lg border-l-2 bg-surface-raised/40 p-4" style={{ borderColor: MODEL_COLORS[k] }}>
              <div className="mb-1.5 flex items-center gap-2 font-medium text-ink"><span style={{ color: MODEL_COLORS[k] }}>{ICONS[k]}</span>{MODEL_LABELS[k]}</div>
              <div className="text-caption text-ink-muted">{MODEL_DESCRIPTIONS[k]}</div>
            </div>
          ))}
        </CardBody>
      </Card>
    </div>
  );
}
