import { Button } from "./Button";

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
      <div className="grid h-14 w-14 place-items-center rounded-xl bg-accent/10 text-accent-300">{icon}</div>
      <div className="font-display text-h3 font-semibold text-ink">{title}</div>
      <div className="max-w-sm text-body text-ink-secondary">{desc}</div>
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

export function SkeletonTable({ rows = 5 }: { rows?: number }) {
  return (
    <div className="overflow-hidden rounded-lg border border-subtle/12 bg-surface">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 border-b border-subtle/8 px-4 py-4 last:border-0">
          <div className="h-4 w-full animate-pulse rounded bg-surface-overlay" style={{ opacity: 1 - i * 0.14 }} />
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
