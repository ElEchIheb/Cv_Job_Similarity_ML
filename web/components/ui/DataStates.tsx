"use client";

import { motion } from "framer-motion";
import { usePrefersReducedMotion } from "@/lib/use-reduced-motion";
import { cn } from "@/lib/utils";
import { Button } from "./Button";

/**
 * Shimmer block — a surface-toned placeholder with a light sweep, so loaders
 * read as part of the same elevation/depth system as real content.
 * The sweep uses the `animate-shimmer` keyframe, which the global
 * prefers-reduced-motion rule freezes to a static block automatically.
 */
export function Shimmer({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return (
    <div className={cn("relative overflow-hidden rounded-md bg-surface-overlay", className)} style={style}>
      <div className="absolute inset-0 -translate-x-full animate-shimmer bg-[linear-gradient(90deg,transparent,rgb(var(--border-subtle)/0.12),transparent)]" />
    </div>
  );
}

/** Fades + lifts real content into place once loading resolves ("settle"). */
export function Settle({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.995 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: "spring", stiffness: 240, damping: 26 }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

/** Slow radar-ping rings for empty-state ambiance. Off under reduced-motion. */
function RadarSweep() {
  const reduced = usePrefersReducedMotion();
  if (reduced) return null;
  return (
    <div className="pointer-events-none absolute inset-0 grid place-items-center" aria-hidden>
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className="absolute rounded-full border border-accent/25"
          initial={{ width: 44, height: 44, opacity: 0 }}
          animate={{ width: 128, height: 128, opacity: [0.5, 0] }}
          transition={{ duration: 3, repeat: Infinity, delay: i, ease: "easeOut" }}
        />
      ))}
    </div>
  );
}

export function EmptyState({
  icon,
  title,
  desc,
  action,
}: {
  icon: React.ReactNode;
  title: string;
  desc: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-xl border border-subtle/12 bg-surface p-11 text-center">
      <div className="relative grid h-14 w-14 place-items-center">
        <RadarSweep />
        <div className="relative grid h-14 w-14 place-items-center rounded-xl bg-accent/10 text-accent-300">{icon}</div>
      </div>
      <div className="font-display text-h3 font-semibold text-ink">{title}</div>
      <div className="max-w-sm text-body text-ink-secondary">{desc}</div>
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

/** Depth skeleton for tables — same border/elevation as the real table, with a
 *  shimmer sweep and per-row/-cell staggered dimming. */
export function SkeletonTable({ rows = 5, cols = 5 }: { rows?: number; cols?: number }) {
  // varied cell widths so it reads like a real table, not equal bars
  const widths = ["38%", "22%", "14%", "16%", "10%"];
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="overflow-hidden rounded-lg border border-subtle/12 bg-surface shadow-e1"
    >
      <div className="flex items-center gap-4 border-b border-subtle/12 px-4 py-3">
        {Array.from({ length: cols }).map((_, c) => (
          <Shimmer key={c} className="h-2.5" style={{ width: widths[c % widths.length] }} />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 border-b border-subtle/8 px-4 py-4 last:border-0" style={{ opacity: 1 - i * 0.12 }}>
          {Array.from({ length: cols }).map((_, c) => (
            <Shimmer key={c} className="h-4" style={{ width: widths[c % widths.length] }} />
          ))}
        </div>
      ))}
    </motion.div>
  );
}

/** Depth skeleton for a stat-card row. */
export function SkeletonStats({ count = 4 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="rounded-lg border border-subtle/12 bg-surface p-5 shadow-e2">
          <Shimmer className="mb-4 h-10 w-10 rounded-lg" />
          <Shimmer className="mb-2 h-7 w-20" />
          <Shimmer className="h-3 w-28" />
        </div>
      ))}
    </div>
  );
}

/** Small inline score bar used in tables (mirrors ui.py progress_mini). */
export function ProgressMini({ value }: { value: number }) {
  const v = value <= 1 ? value * 100 : value;
  const tone = v >= 75 ? "bg-success" : v >= 55 ? "bg-warning" : "bg-danger";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-surface-overlay">
        <div className={`h-full rounded-full ${tone}`} style={{ width: `${Math.min(100, v)}%` }} />
      </div>
      <span className="tnum text-caption font-medium text-ink">{v.toFixed(0)}%</span>
    </div>
  );
}

export { Button };
