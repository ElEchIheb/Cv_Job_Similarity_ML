import { cn } from "@/lib/utils";

type Status = "success" | "warning" | "danger" | "accent" | "neutral";

const styles: Record<Status, string> = {
  // Solid-tinted fills with theme-aware dark-enough text (fg/soft flip per theme)
  success: "bg-success-soft text-success-fg ring-1 ring-success/30",
  warning: "bg-warning-soft text-warning-fg ring-1 ring-warning/30",
  danger: "bg-danger-soft text-danger-fg ring-1 ring-danger/30",
  accent: "bg-accent/12 text-accent-300 ring-1 ring-accent/30",
  neutral: "bg-surface-raised text-ink-secondary ring-1 ring-subtle/15",
};

export function Badge({
  status = "neutral",
  className,
  children,
  dot,
}: {
  status?: Status;
  className?: string;
  children: React.ReactNode;
  dot?: boolean;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-caption font-medium",
        styles[status],
        className,
      )}
    >
      {dot && <span className="h-1.5 w-1.5 rounded-full bg-current" />}
      {children}
    </span>
  );
}
