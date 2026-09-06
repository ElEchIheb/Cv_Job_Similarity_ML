"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Award, FileText, Shield, Sparkles, Target, Users, Zap } from "lucide-react";
import { api } from "@/lib/api/client";
import type { MatchRow, Overview } from "@/lib/api/types";
import { StatCard } from "@/components/ui/StatCard";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { AmbientBackground } from "@/components/three/AmbientBackground";
import { staggerContainer, fadeUp } from "@/lib/motion";
import { BAND_LABEL, DECISION_STATUS } from "@/lib/constants";
import { cn, timeAgo } from "@/lib/utils";

export default function OverviewPage() {
  const [ov, setOv] = useState<Overview | null>(null);
  const [matches, setMatches] = useState<MatchRow[]>([]);

  useEffect(() => {
    api.overview().then(setOv).catch(() => setOv(null));
    api.matches().then(setMatches).catch(() => setMatches([]));
  }, []);

  const avgPct = ov ? (ov.avg_score <= 1 ? ov.avg_score * 100 : ov.avg_score) : 0;
  const dist = (["HIRE", "CONSIDER", "REJECT"] as const).map((d) => ({
    d,
    count: matches.filter((m) => m.decision === d).length,
  }));
  const distTotal = Math.max(1, matches.length);

  return (
    <div className="flex flex-col gap-6">
      {/* ── Hero ─────────────────────────────────────────────── */}
      <motion.section
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ type: "spring", stiffness: 220, damping: 26 }}
        className="relative overflow-hidden rounded-xl border border-subtle/12 bg-surface p-7 shadow-e3 md:p-9"
      >
        <AmbientBackground intensity={0.7} />
        <div className="bg-grid absolute inset-0 opacity-40" />
        <div className="relative z-10 flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
          <div className="max-w-xl">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-subtle/15 glass px-3 py-1 text-caption text-ink-secondary">
              <Sparkles className="h-3.5 w-3.5 text-accent-300" />
              AI-powered recruitment intelligence
            </div>
            <h1 className="font-display text-h1 font-semibold text-ink md:text-display md:leading-[1.05]">
              Evaluate smarter.<br />
              <span className="text-gradient">Hire with confidence.</span>
            </h1>
            <p className="mt-3 text-body-lg text-ink-secondary">
              NeuralHire combines semantic understanding, skill analysis, and gap profiling into
              objective, explainable candidate decisions.
            </p>
          </div>
          <div className="flex gap-3">
            <Link href="/analysis">
              <Button size="lg" icon={<Target className="h-4 w-4" />}>Run Evaluation</Button>
            </Link>
            <Link href="/leaderboard">
              <Button size="lg" variant="secondary" icon={<Users className="h-4 w-4" />}>Rank Candidates</Button>
            </Link>
          </div>
        </div>
      </motion.section>

      {/* ── Stat cards (dashboard.py stats) ──────────────────── */}
      <motion.div
        variants={staggerContainer(0.05)}
        initial="hidden"
        animate="show"
        className="grid grid-cols-2 gap-4 lg:grid-cols-5"
      >
        <StatCard label="Candidates Evaluated" value={ov?.total_candidates ?? 0} icon={<Users className="h-5 w-5" />} tone="accent" />
        <StatCard label="Avg. Compatibility" value={avgPct} suffix="%" decimals={1} icon={<Award className="h-5 w-5" />} tone="success" />
        <StatCard label="HIRE Rate" value={ov?.hire_pct ?? 0} suffix="%" decimals={1} icon={<Shield className="h-5 w-5" />} tone="cyan" />
        <StatCard label="Active Job Offers" value={ov?.total_jobs ?? 0} icon={<Zap className="h-5 w-5" />} tone="warning" />
        <StatCard label="Total Match Reports" value={ov?.total_matches ?? 0} icon={<FileText className="h-5 w-5" />} tone="accent" />
      </motion.div>

      {/* ── Recent + distribution ────────────────────────────── */}
      <div className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
        <Card elevation={2}>
          <CardHeader>
            <CardTitle>Recent analyses</CardTitle>
            <Link href="/history" className="text-caption text-accent-300 hover:underline">View all</Link>
          </CardHeader>
          <CardBody className="flex flex-col gap-1">
            {matches.length === 0 && (
              <div className="py-8 text-center text-body text-ink-muted">
                No evaluations yet. <Link href="/analysis" className="text-accent-300 hover:underline">Run your first evaluation →</Link>
              </div>
            )}
            {matches.slice(0, 6).map((m, i) => {
              const status = m.decision ? DECISION_STATUS[m.decision] : "neutral";
              return (
                <motion.div
                  key={m.id}
                  variants={fadeUp}
                  initial="hidden"
                  animate="show"
                  transition={{ delay: i * 0.04 }}
                  className="flex items-center gap-4 rounded-lg px-3 py-2.5 transition-colors hover:bg-surface-raised/60"
                >
                  <div className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-surface-overlay text-caption font-semibold text-ink-secondary">
                    {m.candidate_name?.slice(0, 1) ?? "?"}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="truncate font-medium text-ink">{m.candidate_name}</div>
                    <div className="truncate text-caption text-ink-muted">{m.job_title}</div>
                  </div>
                  <div className="tnum text-right font-display text-h4 font-semibold text-ink">
                    {Math.round((m.final_score ?? 0) * 100)}%
                  </div>
                  {m.decision && (
                    <Badge status={status as "success" | "warning" | "danger"} className="w-[92px] justify-center">
                      {BAND_LABEL[m.decision]}
                    </Badge>
                  )}
                  <div className="hidden w-16 text-right text-caption text-ink-muted sm:block">
                    {m.created_at ? timeAgo(m.created_at) : ""}
                  </div>
                </motion.div>
              );
            })}
          </CardBody>
        </Card>

        <Card elevation={2}>
          <CardHeader><CardTitle>Decision mix</CardTitle></CardHeader>
          <CardBody className="flex flex-col gap-5">
            {dist.map(({ d, count }) => {
              const s = DECISION_STATUS[d];
              const pct = (count / distTotal) * 100;
              return (
                <div key={d}>
                  <div className="mb-1.5 flex items-center justify-between text-caption">
                    <span className="flex items-center gap-2 text-ink-secondary">
                      <span className={cn("h-2 w-2 rounded-full", s === "success" ? "bg-success" : s === "warning" ? "bg-warning" : "bg-danger")} />
                      {BAND_LABEL[d]}
                    </span>
                    <span className="tnum font-medium text-ink">{count}</span>
                  </div>
                  <div className="h-2.5 overflow-hidden rounded-full bg-surface-overlay">
                    <motion.div
                      className={cn("h-full rounded-full", s === "success" ? "bg-success" : s === "warning" ? "bg-warning" : "bg-danger")}
                      initial={{ width: 0 }}
                      animate={{ width: `${pct}%` }}
                      transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
                    />
                  </div>
                </div>
              );
            })}
            <div className="mt-1 rounded-lg bg-surface-raised/60 p-4">
              <div className="text-caption text-ink-secondary">Total evaluations</div>
              <div className="mt-1 font-display text-h2 font-semibold text-ink tnum">{ov?.total_matches ?? 0}</div>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
