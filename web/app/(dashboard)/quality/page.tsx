"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Award, BarChart3, Gauge, Info, Timer, TrendingUp } from "lucide-react";
import { api } from "@/lib/api/client";
import type { Quality, QualityFigure } from "@/lib/api/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/DataStates";
import { usePrefersReducedMotion } from "@/lib/use-reduced-motion";
import { staggerContainer, fadeUp } from "@/lib/motion";
import { cn } from "@/lib/utils";

const MODEL_LABEL = (name: string): string => {
  const m: Record<string, string> = {
    hybrid: "Overall AI Match", embedding: "Semantic Relevance", tfidf: "Keyword Relevance", skill: "Skills Assessment",
  };
  return m[name.toLowerCase()] ?? name.replace(/\b\w/g, (c) => c.toUpperCase());
};

export default function QualityPage() {
  const [q, setQ] = useState<Quality | null>(null);
  const [figures, setFigures] = useState<QualityFigure[]>([]);
  const [figUrls, setFigUrls] = useState<Record<string, string>>({});
  const [tab, setTab] = useState<"ci" | "subgroup" | "error">("ci");

  useEffect(() => {
    api.quality().then(setQ).catch(() => setQ({ available: false }));
    api.qualityFigures().then(async (figs) => {
      setFigures(figs);
      const urls: Record<string, string> = {};
      for (const f of figs) { try { urls[f.name] = await api.figureBlob(f.name); } catch { /* skip */ } }
      setFigUrls(urls);
    }).catch(() => {});
  }, []);

  if (!q) return <div className="py-16 text-center text-ink-muted">Loading benchmark results…</div>;
  if (!q.available || !q.metrics) {
    return (
      <div className="flex flex-col gap-6">
        <PageHeader badge="AI Quality Center" title="AI System" highlight="Quality & Reliability" subtitle="Executive quality benchmarks across all evaluation dimensions." />
        <EmptyState icon={<TrendingUp className="h-8 w-8" />} title="No benchmark results available yet" desc="Run the evaluation suite to generate performance metrics." />
      </div>
    );
  }

  const entries = Object.entries(q.metrics);
  const bestF1 = entries.reduce((b, [n, m]) => ((m.f1 ?? 0) > (b.val) ? { name: n, val: m.f1 ?? 0 } : b), { name: "", val: -1 });
  const bestAcc = entries.reduce((b, [, m]) => Math.max(b, m.accuracy ?? 0), 0);
  const bestAuc = entries.reduce((b, [, m]) => Math.max(b, m.roc_auc ?? 0), 0);
  const fastest = entries.reduce((b, [, m]) => Math.min(b, m.inference_ms_per_pair ?? 9999), 9999);

  const an = q.analysis ?? {};

  return (
    <div className="flex flex-col gap-6">
      <PageHeader badge="AI Quality Center" title="AI System" highlight="Quality & Reliability"
        subtitle="Executive quality benchmarks across all evaluation dimensions — accuracy, decision reliability, precision, and response latency." />

      {q.provenance && (
        <div className="flex items-start gap-3 rounded-lg border border-subtle/12 bg-accent/8 px-4 py-3 text-caption text-ink-secondary ring-1 ring-accent/10">
          <Info className="mt-0.5 h-4 w-4 shrink-0 text-accent-300" />
          <span>Source: offline evaluation run — {q.provenance.source}, generated {q.provenance.generated}.
            {q.provenance.n_samples ? ` Test set: ${q.provenance.n_samples} pairs.` : ""} These figures reflect the last benchmark run on the held-out dataset — they are not recomputed live.</span>
        </div>
      )}

      {/* Performance summary with per-metric bars */}
      <Card elevation={2}>
        <CardHeader><CardTitle className="flex items-center gap-2 text-h4"><BarChart3 className="h-4 w-4" /> Model performance summary</CardTitle></CardHeader>
        <CardBody className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-body">
            <thead><tr className="border-b border-subtle/12 text-caption uppercase tracking-wide text-ink-muted">
              <th className="px-3 py-2 text-left">Evaluation Method</th>
              {["Accuracy", "Precision", "Recall", "F1 Score", "AUC-ROC", "Inference (ms/pair)"].map((h) => <th key={h} className="px-3 py-2 text-left">{h}</th>)}
            </tr></thead>
            <tbody>
              {entries.map(([name, m]) => (
                <tr key={name} className="border-b border-subtle/8 last:border-0">
                  <td className="px-3 py-3 font-medium text-ink">{MODEL_LABEL(name)}</td>
                  <MetricCell pct={(m.accuracy ?? 0) * 100} />
                  <MetricCell pct={(m.precision ?? 0) * 100} />
                  <MetricCell pct={(m.recall ?? 0) * 100} />
                  <MetricCell pct={(m.f1 ?? 0) * 100} highlight={name === bestF1.name} />
                  <td className="px-3 py-3 tnum text-ink-secondary">{(m.roc_auc ?? 0).toFixed(3)}</td>
                  <td className="px-3 py-3 tnum text-ink-secondary">{(m.inference_ms_per_pair ?? 0).toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardBody>
      </Card>

      {/* Highlights */}
      <motion.div variants={staggerContainer(0.06)} initial="hidden" animate="show" className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Highlight icon={<Gauge className="h-4 w-4" />} label="Best Accuracy" value={`${(bestAcc * 100).toFixed(1)}%`} desc="Highest classification accuracy" tone="success" />
        <Highlight icon={<Award className="h-4 w-4" />} label="Best F1 Score" value={`${(bestF1.val * 100).toFixed(1)}%`} desc={`Best balanced precision/recall — ${MODEL_LABEL(bestF1.name)}`} tone="accent" />
        <Highlight icon={<TrendingUp className="h-4 w-4" />} label="Best AUC-ROC" value={bestAuc.toFixed(3)} desc="Ranking quality (1.0 = perfect)" tone="cyan" />
        <Highlight icon={<Timer className="h-4 w-4" />} label="Fastest Method" value={`${fastest.toFixed(1)} ms`} desc="Offline inference latency per pair" tone="warning" />
      </motion.div>

      {/* Figures */}
      {figures.length > 0 && (
        <Card elevation={2}>
          <CardHeader><CardTitle className="text-h4">Evaluation charts</CardTitle></CardHeader>
          <CardBody className="grid gap-4 sm:grid-cols-2">
            {figures.map((f) => (
              <div key={f.name}>
                <div className="mb-1.5 text-micro font-semibold uppercase tracking-wide text-ink-muted">{f.label}</div>
                {figUrls[f.name]
                  ? <img src={figUrls[f.name]} alt={f.label} className="w-full rounded-lg border border-subtle/12 bg-white" />
                  : <div className="h-40 animate-pulse rounded-lg bg-surface-overlay" />}
              </div>
            ))}
          </CardBody>
        </Card>
      )}

      {/* Scientific analysis tabs */}
      {(an.bootstrap_ci || an.subgroup_analysis || an.error_analysis) && (
        <Card elevation={2}>
          <CardHeader>
            <div className="flex gap-1 rounded-lg bg-surface-overlay p-0.5">
              {([["ci", "Confidence Intervals"], ["subgroup", "Subgroup Performance"], ["error", "Error Analysis"]] as const).map(([k, l]) => (
                <button key={k} onClick={() => setTab(k)}
                  className={cn("rounded-md px-3 py-1.5 text-caption font-medium transition-colors", tab === k ? "bg-surface text-ink shadow-e1" : "text-ink-muted hover:text-ink-secondary")}>{l}</button>
              ))}
            </div>
          </CardHeader>
          <CardBody>
            {tab === "ci" && an.bootstrap_ci && (
              <div className="overflow-x-auto">
                <p className="mb-3 text-caption text-ink-secondary"><strong className="text-ink">Bootstrap 95% Confidence Intervals</strong> — ensures metrics are statistically robust and not due to chance.</p>
                <table className="w-full min-w-[480px] text-body">
                  <thead><tr className="border-b border-subtle/12 text-caption uppercase tracking-wide text-ink-muted">
                    <th className="px-3 py-2 text-left">Model</th><th className="px-3 py-2 text-left">F1 Score</th><th className="px-3 py-2 text-left">AUC-ROC</th><th className="px-3 py-2 text-left">Accuracy</th>
                  </tr></thead>
                  <tbody>
                    {Object.entries(an.bootstrap_ci).map(([name, d]) => (
                      <tr key={name} className="border-b border-subtle/8 last:border-0">
                        <td className="px-3 py-2.5 font-medium text-ink">{MODEL_LABEL(name)}</td>
                        <td className="px-3 py-2.5 tnum text-ink-secondary">[{(d.f1?.[0] ?? 0).toFixed(2)} – {(d.f1?.[1] ?? 0).toFixed(2)}]</td>
                        <td className="px-3 py-2.5 tnum text-ink-secondary">[{(d.roc_auc?.[0] ?? 0).toFixed(2)} – {(d.roc_auc?.[1] ?? 0).toFixed(2)}]</td>
                        <td className="px-3 py-2.5 tnum text-ink-secondary">[{(d.accuracy?.[0] ?? 0).toFixed(2)} – {(d.accuracy?.[1] ?? 0).toFixed(2)}]</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {tab === "subgroup" && (
              <div className="grid gap-6 md:grid-cols-2">
                <SubgroupTable title="Performance by Seniority" col="Seniority" data={an.subgroup_analysis?.seniority_performance} />
                <SubgroupTable title="Performance by Domain" col="Domain" data={an.subgroup_analysis?.domain_performance} />
              </div>
            )}
            {tab === "error" && an.error_analysis && (
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-lg border-l-2 border-danger bg-surface-raised/40 p-4">
                  <div className="font-display text-h2 font-bold text-danger-fg tnum">{an.error_analysis.fp_count ?? 0}</div>
                  <div className="text-caption text-ink-secondary">False Positives</div>
                  {an.error_analysis.dominant_fp_domain && <div className="mt-1 text-caption text-ink-muted">Most common domain: {an.error_analysis.dominant_fp_domain}</div>}
                </div>
                <div className="rounded-lg border-l-2 border-accent bg-surface-raised/40 p-4">
                  <div className="font-display text-h2 font-bold text-accent-300 tnum">{an.error_analysis.fn_count ?? 0}</div>
                  <div className="text-caption text-ink-secondary">False Negatives</div>
                  {an.error_analysis.dominant_fn_domain && <div className="mt-1 text-caption text-ink-muted">Most common domain: {an.error_analysis.dominant_fn_domain}</div>}
                </div>
              </div>
            )}
          </CardBody>
        </Card>
      )}
    </div>
  );
}

function MetricCell({ pct, highlight }: { pct: number; highlight?: boolean }) {
  const reduced = usePrefersReducedMotion();
  const w = `${Math.min(100, pct)}%`;
  return (
    <td className="px-3 py-3">
      <div className="flex items-center gap-2">
        <div className="h-1.5 w-14 overflow-hidden rounded-full bg-surface-overlay">
          <motion.div
            className={cn("h-full rounded-full", highlight ? "bg-gradient-to-r from-accent-400 to-cyan-400" : "bg-accent/60")}
            initial={{ width: reduced ? w : 0 }}
            whileInView={{ width: w }}
            viewport={{ once: true }}
            transition={reduced ? { duration: 0 } : { duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
          />
        </div>
        <span className={cn("tnum text-caption font-medium", highlight ? "text-accent-300" : "text-ink")}>{pct.toFixed(1)}%</span>
      </div>
    </td>
  );
}

function Highlight({ icon, label, value, desc, tone }: { icon: React.ReactNode; label: string; value: string; desc: string; tone: string }) {
  const t: Record<string, string> = { accent: "text-accent-300 bg-accent/12", success: "text-success-fg bg-success-soft", warning: "text-warning-fg bg-warning-soft", cyan: "text-cyan-400 bg-cyan-500/12" };
  return (
    <motion.div
      variants={fadeUp}
      whileHover={{ y: -4 }}
      transition={{ type: "spring", stiffness: 300, damping: 24 }}
      className="rounded-xl border border-subtle/12 bg-surface p-5 shadow-e2 transition-shadow hover:shadow-e4"
    >
      <span className={cn("mb-2 inline-grid h-8 w-8 place-items-center rounded-lg", t[tone])}>{icon}</span>
      <div className="font-display text-h2 font-semibold text-ink">{value}</div>
      <div className="text-caption font-medium text-ink-secondary">{label}</div>
      <div className="mt-1 text-caption text-ink-muted">{desc}</div>
    </motion.div>
  );
}

function SubgroupTable({ title, col, data }: { title: string; col: string; data?: Record<string, { count: number; auc: number }> }) {
  const rows = Object.entries(data ?? {});
  return (
    <div>
      <div className="mb-2 font-medium text-ink">{title}</div>
      {rows.length === 0 ? <div className="text-caption text-ink-muted">No {col.toLowerCase()} labels in the dataset.</div> : (
        <table className="w-full text-body">
          <thead><tr className="border-b border-subtle/12 text-caption uppercase tracking-wide text-ink-muted">
            <th className="px-2 py-1.5 text-left">{col}</th><th className="px-2 py-1.5 text-right">Samples</th><th className="px-2 py-1.5 text-right">AUC</th>
          </tr></thead>
          <tbody>
            {rows.map(([k, v]) => (
              <tr key={k} className="border-b border-subtle/8 last:border-0">
                <td className="px-2 py-1.5 text-ink">{k}</td><td className="px-2 py-1.5 text-right tnum text-ink-secondary">{v.count}</td><td className="px-2 py-1.5 text-right tnum text-ink-secondary">{v.auc.toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
