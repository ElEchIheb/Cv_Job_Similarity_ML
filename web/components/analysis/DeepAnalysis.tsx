"use client";

/**
 * AI Deep Analysis — Layer 2 (LLM qualitative reasoning).
 *
 * Additive section on the Candidate Analysis result page. It loads AFTER the
 * main score/verdict render (separate API call) and shows its OWN loading /
 * unavailable / error states, so it can never block or degrade the already
 * verified statistical result UI above it.
 */
import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  Sparkles, AlertTriangle, Lightbulb, MessageSquareQuote, TrendingUp,
  CloudOff, RefreshCcw, ScrollText,
} from "lucide-react";
import { api } from "@/lib/api/client";
import type { DeepAnalysisEnvelope } from "@/lib/api/types";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { staggerContainer, fadeUp } from "@/lib/motion";
import { cn } from "@/lib/utils";

type State =
  | { phase: "loading" }
  | { phase: "done"; env: DeepAnalysisEnvelope };

export function DeepAnalysis({ matchId }: { matchId: number | null }) {
  const [state, setState] = useState<State>({ phase: "loading" });
  const requested = useRef<number | null>(null);

  const load = async () => {
    if (matchId == null) {
      setState({
        phase: "done",
        env: {
          status: "unavailable", model: "", generated_at: null, latency_ms: null,
          analysis: null, error: "This evaluation was not persisted, so deep analysis is unavailable.",
        },
      });
      return;
    }
    setState({ phase: "loading" });
    try {
      const res = await api.deepAnalysis(matchId);
      setState({ phase: "done", env: res.ai_deep_analysis });
    } catch (err) {
      setState({
        phase: "done",
        env: {
          status: "error", model: "", generated_at: null, latency_ms: null, analysis: null,
          error: err instanceof Error ? err.message : "Deep analysis request failed.",
        },
      });
    }
  };

  // Fire once per match id.
  useEffect(() => {
    if (requested.current === matchId) return;
    requested.current = matchId;
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [matchId]);

  return (
    <Card elevation={2} className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-24 bg-[linear-gradient(120deg,#7c5cff22,#22cfee18)] opacity-70 blur-2xl" />
      <CardHeader className="relative">
        <div className="flex items-center gap-2">
          <div className="grid h-8 w-8 place-items-center rounded-lg bg-accent/12 text-accent-300 ring-1 ring-accent/20">
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <CardTitle>AI Deep Analysis</CardTitle>
            <div className="text-caption text-ink-muted">Qualitative reasoning layer · local LLM</div>
          </div>
        </div>
        {state.phase === "done" && state.env.status === "ok" && state.env.model && (
          <Badge status="accent" dot>{state.env.model}</Badge>
        )}
      </CardHeader>
      <CardBody className="relative">
        {state.phase === "loading" ? (
          <LoadingState />
        ) : state.env.status === "ok" && state.env.analysis ? (
          <Loaded env={state.env} />
        ) : (
          <Unavailable env={state.env} onRetry={load} />
        )}
      </CardBody>
    </Card>
  );
}

function LoadingState() {
  return (
    <div className="flex flex-col items-center gap-3 py-8">
      <div className="relative h-11 w-11">
        <div className="absolute inset-0 animate-spin rounded-full border-2 border-accent/20 border-t-accent" />
        <Sparkles className="absolute inset-0 m-auto h-4 w-4 text-accent-300" />
      </div>
      <div className="text-center">
        <div className="font-medium text-ink">Reasoning over the profile…</div>
        <div className="mt-0.5 text-caption text-ink-muted">
          Local inference can take 10–60s on CPU. The score above is already final.
        </div>
      </div>
      <div className="mt-1 flex flex-wrap justify-center gap-2">
        {["Career trajectory", "Red flags", "Recommendations", "Interview questions"].map((s) => (
          <span key={s} className="rounded-full bg-surface-raised px-3 py-1 text-caption text-ink-muted">{s}</span>
        ))}
      </div>
    </div>
  );
}

function Unavailable({ env, onRetry }: { env: DeepAnalysisEnvelope; onRetry: () => void }) {
  const isDisabled = env.status === "disabled";
  return (
    <div className="flex flex-col items-center gap-3 py-8 text-center">
      <div className="grid h-11 w-11 place-items-center rounded-full bg-surface-raised text-ink-muted ring-1 ring-subtle/15">
        <CloudOff className="h-5 w-5" />
      </div>
      <div>
        <div className="font-medium text-ink">AI analysis unavailable</div>
        <div className="mx-auto mt-1 max-w-md text-caption text-ink-secondary">
          {env.error || "The local LLM runtime could not be reached."}
        </div>
        {!isDisabled && (
          <div className="mx-auto mt-2 max-w-md rounded-lg bg-surface-raised/60 px-3 py-2 text-left text-caption text-ink-muted">
            Setup: install <span className="text-ink-secondary">Ollama</span>, run{" "}
            <code className="text-accent-300">ollama serve</code>, then{" "}
            <code className="text-accent-300">ollama pull llama3.2:3b</code>.
          </div>
        )}
      </div>
      {!isDisabled && (
        <Button variant="secondary" size="sm" icon={<RefreshCcw className="h-3.5 w-3.5" />} onClick={onRetry}>
          Retry
        </Button>
      )}
    </div>
  );
}

function Loaded({ env }: { env: DeepAnalysisEnvelope }) {
  const a = env.analysis!;
  const sevTone = (s: string): "danger" | "warning" | "neutral" =>
    /high/i.test(s) ? "danger" : /med/i.test(s) ? "warning" : "neutral";

  return (
    <motion.div variants={staggerContainer(0.08)} initial="hidden" animate="show" className="flex flex-col gap-5">
      {/* Fit justification — the headline synthesis */}
      <motion.div variants={fadeUp} className="rounded-lg border border-accent/15 bg-accent/6 p-4">
        <div className="mb-1.5 flex items-center gap-2 text-caption font-medium text-accent-300">
          <ScrollText className="h-3.5 w-3.5" /> Recruiter summary
        </div>
        <p className="text-body text-ink-secondary">{a.fit_justification || "—"}</p>
      </motion.div>

      {/* Career trajectory */}
      <motion.div variants={fadeUp}>
        <SectionTitle icon={<TrendingUp className="h-4 w-4" />} title="Career trajectory" />
        <div className="rounded-lg bg-surface-raised/50 p-4">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            {a.career_trajectory.seniority_signal && (
              <Badge status="accent">{a.career_trajectory.seniority_signal}</Badge>
            )}
          </div>
          <p className="text-body text-ink-secondary">{a.career_trajectory.summary || "—"}</p>
          {a.career_trajectory.progression && (
            <p className="mt-2 text-caption text-ink-muted">{a.career_trajectory.progression}</p>
          )}
        </div>
      </motion.div>

      <div className="grid gap-5 lg:grid-cols-2">
        {/* Red flags */}
        <motion.div variants={fadeUp}>
          <SectionTitle icon={<AlertTriangle className="h-4 w-4" />} title="Red flags & inconsistencies" />
          <div className="flex flex-col gap-2">
            {a.red_flags.length === 0 && (
              <div className="rounded-lg bg-surface-raised/50 p-3 text-body text-ink-muted">None flagged.</div>
            )}
            {a.red_flags.map((f, i) => (
              <div key={i} className="rounded-lg border border-subtle/12 bg-surface-raised/50 p-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium text-ink">{f.issue}</span>
                  {f.severity && <Badge status={sevTone(f.severity)}>{f.severity}</Badge>}
                </div>
                {f.evidence && <p className="mt-1 text-caption text-ink-muted">{f.evidence}</p>}
              </div>
            ))}
          </div>
        </motion.div>

        {/* Recommendations */}
        <motion.div variants={fadeUp}>
          <SectionTitle icon={<Lightbulb className="h-4 w-4" />} title="Personalized recommendations" />
          <div className="flex flex-col gap-2">
            {a.recommendations.length === 0 && (
              <div className="rounded-lg bg-surface-raised/50 p-3 text-body text-ink-muted">—</div>
            )}
            {a.recommendations.map((r, i) => (
              <div key={i} className="rounded-lg border border-subtle/12 bg-surface-raised/50 p-3">
                <div className="flex gap-2 text-body text-ink">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent-400" />
                  <span className="font-medium">{r.recommendation}</span>
                </div>
                {r.rationale && <p className="ml-3.5 mt-1 text-caption text-ink-muted">{r.rationale}</p>}
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Interview questions */}
      <motion.div variants={fadeUp}>
        <SectionTitle icon={<MessageSquareQuote className="h-4 w-4" />} title="Tailored interview questions" />
        <ol className="flex flex-col gap-2">
          {a.interview_questions.map((q, i) => (
            <li key={i} className="flex gap-3 rounded-lg bg-surface-raised/50 p-3">
              <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-accent/12 text-caption font-semibold text-accent-300">
                {i + 1}
              </span>
              <div>
                <div className="text-body text-ink">{q.question}</div>
                {q.targets && <div className="mt-0.5 text-caption text-ink-muted">Probes: {q.targets}</div>}
              </div>
            </li>
          ))}
        </ol>
      </motion.div>

      <div className="flex items-center gap-2 border-t border-subtle/10 pt-3 text-caption text-ink-muted">
        <Sparkles className="h-3.5 w-3.5" />
        Qualitative second opinion from a local LLM ({env.model}
        {env.latency_ms != null ? ` · ${(env.latency_ms / 1000).toFixed(1)}s` : ""}). It does not
        change the statistical score or decision above.
      </div>
    </motion.div>
  );
}

function SectionTitle({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <div className={cn("mb-2 flex items-center gap-2 text-caption font-semibold text-ink-secondary")}>
      <span className="text-accent-300">{icon}</span>
      {title}
    </div>
  );
}
