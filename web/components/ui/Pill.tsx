import { cn } from "@/lib/utils";

type PillTone = "matched" | "missing" | "extra" | "priority" | "neutral";

const tones: Record<PillTone, string> = {
  matched: "bg-success-soft text-success-fg ring-1 ring-success/30",
  missing: "bg-warning-soft text-warning-fg ring-1 ring-warning/30",
  priority: "bg-danger-soft text-danger-fg ring-1 ring-danger/35",
  extra: "bg-accent/12 text-accent-300 ring-1 ring-accent/25",
  neutral: "bg-surface-raised text-ink-secondary ring-1 ring-subtle/12",
};

/** Skill chip — real contrast in both themes via soft/fg token pairs. */
export function Pill({
  tone = "neutral",
  className,
  children,
  icon,
}: {
  tone?: PillTone;
  className?: string;
  children: React.ReactNode;
  icon?: React.ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-caption font-medium",
        tones[tone],
        className,
      )}
    >
      {icon}
      {children}
    </span>
  );
}
