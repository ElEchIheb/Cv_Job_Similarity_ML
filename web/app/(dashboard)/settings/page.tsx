"use client";

import { useEffect, useState } from "react";
import { Brain, CheckCircle2, Cpu, Info, Layers, Search, SlidersHorizontal, Zap } from "lucide-react";
import { api } from "@/lib/api/client";
import type { ModelKey, SystemInfo } from "@/lib/api/types";
import { useDecisionConfig } from "@/lib/decision-config";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";
import { MODEL_COLORS } from "@/lib/constants";
import { cn } from "@/lib/utils";

const MODEL_ICON: Record<ModelKey, React.ReactNode> = {
  hybrid: <Zap className="h-4 w-4" />, embedding: <Brain className="h-4 w-4" />,
  tfidf: <Search className="h-4 w-4" />, skill: <Layers className="h-4 w-4" />,
};

type Tab = "thresholds" | "models" | "system" | "about";

export default function SettingsPage() {
  const toast = useToast();
  const cfg = useDecisionConfig();
  const [tab, setTab] = useState<Tab>("thresholds");
  const [system, setSystem] = useState<SystemInfo | null>(null);
  const [strong, setStrong] = useState(cfg.strong);
  const [potential, setPotential] = useState(cfg.potential);

  useEffect(() => { api.system().then(setSystem).catch(() => {}); }, []);
  useEffect(() => { setStrong(cfg.strong); setPotential(cfg.potential); }, [cfg.strong, cfg.potential]);

  // keep potential strictly below strong (mirrors the Streamlit slider bounds)
  useEffect(() => { if (potential > strong - 1) setPotential(strong - 1); }, [strong]); // eslint-disable-line

  const apply = () => {
    cfg.setConfig(potential, strong);
    toast("success", `Active decision policy updated: Strong Fit ≥ ${strong}%, Potential Fit ${potential}–${strong - 1}%.`);
  };

  return (
    <div className="flex flex-col gap-6">
      <PageHeader badge="Enterprise Settings" title="Platform" highlight="Settings"
        subtitle="Configure decision thresholds, review AI system parameters, and manage platform preferences." />

      <div className="flex flex-wrap gap-1 rounded-lg bg-surface-overlay p-0.5">
        {([["thresholds", "Decision Thresholds"], ["models", "AI Models"], ["system", "System Status"], ["about", "About"]] as const).map(([k, l]) => (
          <button key={k} onClick={() => setTab(k)}
            className={cn("rounded-md px-4 py-2 text-caption font-medium transition-colors", tab === k ? "bg-surface text-ink shadow-e1" : "text-ink-muted hover:text-ink-secondary")}>{l}</button>
        ))}
      </div>

      {tab === "thresholds" && (
        <div className="grid gap-5 lg:grid-cols-2">
          <Card elevation={2}>
            <CardHeader><CardTitle className="flex items-center gap-2 text-h4"><SlidersHorizontal className="h-4 w-4" /> Decision thresholds</CardTitle></CardHeader>
            <CardBody className="flex flex-col gap-5">
              <div className="flex items-start gap-3 rounded-lg bg-accent/8 px-3 py-2.5 text-caption text-ink-secondary ring-1 ring-accent/10">
                <Info className="mt-0.5 h-4 w-4 shrink-0 text-accent-300" />
                <span>These thresholds are the single source of truth for the Strong Fit / Potential Fit / Low Fit decision. They affect every <strong>future</strong> evaluation this session. Previously saved evaluations keep the thresholds they were scored with.</span>
              </div>
              <div>
                <div className="mb-1.5 flex items-center justify-between text-caption">
                  <span className="text-ink-secondary">Strong Fit threshold (%)</span><span className="tnum font-semibold text-success-fg">{strong}%</span>
                </div>
                <input type="range" min={50} max={95} value={strong} onChange={(e) => setStrong(Number(e.target.value))} className="w-full accent-[#7c5cff]" />
              </div>
              <div>
                <div className="mb-1.5 flex items-center justify-between text-caption">
                  <span className="text-ink-secondary">Potential Fit threshold (%)</span><span className="tnum font-semibold text-warning-fg">{potential}%</span>
                </div>
                <input type="range" min={10} max={strong - 1} value={potential} onChange={(e) => setPotential(Number(e.target.value))} className="w-full accent-[#7c5cff]" />
              </div>
              <Button onClick={apply}>Apply thresholds</Button>
              <p className="text-caption text-ink-muted">Currently active — Strong Fit ≥ {cfg.strong}%, Potential Fit ≥ {cfg.potential}%.</p>
            </CardBody>
          </Card>

          <Card elevation={2}>
            <CardHeader><CardTitle className="text-h4">Threshold preview</CardTitle></CardHeader>
            <CardBody className="flex flex-col gap-3">
              <PreviewRow band="Strong Fit" range={`≥ ${strong}%`} tone="success" tag="Recommended" />
              <PreviewRow band="Potential Fit" range={`${potential}% – ${strong - 1}%`} tone="warning" tag="Consider" />
              <PreviewRow band="Low Fit" range={`Below ${potential}%`} tone="danger" tag="Not Recommended" />
            </CardBody>
          </Card>
        </div>
      )}

      {tab === "models" && (
        <div className="grid gap-4 md:grid-cols-2">
          {(system?.models ?? []).map((m) => (
            <Card key={m.key} elevation={2} className="border-l-4" style={{ borderLeftColor: MODEL_COLORS[m.key] }}>
              <CardBody className="flex items-start gap-4">
                <span className="grid h-10 w-10 shrink-0 place-items-center rounded-lg" style={{ color: MODEL_COLORS[m.key], background: `${MODEL_COLORS[m.key]}1f` }}>{MODEL_ICON[m.key]}</span>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-display text-h4 font-semibold text-ink">{m.label}</span>
                    <Badge status="success">{m.status}</Badge>
                  </div>
                  <p className="mt-1 text-caption text-ink-secondary">{m.description}</p>
                </div>
              </CardBody>
            </Card>
          ))}
        </div>
      )}

      {tab === "system" && (
        <div className="grid gap-5 lg:grid-cols-2">
          <Card elevation={2}>
            <CardHeader><CardTitle className="flex items-center gap-2 text-h4"><Cpu className="h-4 w-4" /> Environment</CardTitle></CardHeader>
            <CardBody className="flex flex-col gap-3 text-body">
              <Row label="Python" value={system?.python_version ?? "…"} />
              <Row label="Match threshold" value={system ? String(system.config.match_threshold) : "…"} />
              <Row label="Embedding model" value={system?.config.embedding_model ?? "…"} />
              <Row label="Rate limit" value={system ? `${system.config.rate_limit} req/min` : "…"} />
            </CardBody>
          </Card>
          <Card elevation={2}>
            <CardHeader><CardTitle className="text-h4">Model status</CardTitle></CardHeader>
            <CardBody className="flex flex-col gap-2">
              {(system?.models ?? []).map((m) => (
                <div key={m.key} className="flex items-center justify-between border-b border-subtle/8 pb-2 last:border-0">
                  <span className="flex items-center gap-2 text-body text-ink"><CheckCircle2 className="h-4 w-4 text-success-fg" />{m.label}</span>
                  <Badge status="success">{m.status}</Badge>
                </div>
              ))}
            </CardBody>
          </Card>
        </div>
      )}

      {tab === "about" && (
        <Card elevation={2}>
          <CardBody className="flex flex-col gap-4 p-8">
            <div className="font-display text-h1 font-bold text-ink">Neural<span className="text-gradient">Hire</span></div>
            <div className="text-micro font-semibold uppercase tracking-[0.16em] text-ink-muted">Enterprise Edition · v4.0</div>
            <p className="max-w-xl text-body-lg text-ink-secondary">
              NeuralHire is an AI-powered recruitment evaluation platform designed to help HR professionals screen, compare, and rank candidates objectively and efficiently — built with three complementary evaluation engines (keyword, semantic, and skills detection) combined into a single explainable compatibility score.
            </p>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {[
                ["AI Matching", "Three complementary algorithms — keyword, semantic, and skills-based"],
                ["Explainability", "Gap analysis, competency profiling, and decision justification"],
                ["Multilingual", "English and French CV/JD support"],
                ["Bulk Processing", "Evaluate multiple candidates via file upload"],
                ["Report Generation", "Professional PDF reports with charts and recommendations"],
                ["REST API", "Full API access for integration with existing HR systems"],
              ].map(([t, d]) => (
                <div key={t} className="rounded-lg border border-subtle/10 bg-surface-raised/40 p-3">
                  <div className="font-medium text-ink">{t}</div>
                  <div className="text-caption text-ink-muted">{d}</div>
                </div>
              ))}
            </div>
            <div className="text-caption text-ink-muted">Final year engineering project (PFE) · AI Recruitment Intelligence</div>
          </CardBody>
        </Card>
      )}
    </div>
  );
}

function PreviewRow({ band, range, tone, tag }: { band: string; range: string; tone: "success" | "warning" | "danger"; tag: string }) {
  const dot = tone === "success" ? "bg-success" : tone === "warning" ? "bg-warning" : "bg-danger";
  return (
    <div className="flex items-center justify-between rounded-lg border border-subtle/10 bg-surface-raised/40 p-3">
      <div className="flex items-center gap-2.5">
        <span className={cn("h-2.5 w-2.5 rounded-full", dot)} />
        <span className="font-medium text-ink">{band}</span>
      </div>
      <span className="tnum text-caption text-ink-secondary">{range}</span>
      <Badge status={tone}>{tag}</Badge>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-subtle/8 pb-2.5 last:border-0">
      <span className="text-ink-secondary">{label}</span>
      <span className="font-medium text-ink">{value}</span>
    </div>
  );
}
