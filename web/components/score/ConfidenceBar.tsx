"use client";

import { motion } from "framer-motion";
import { usePrefersReducedMotion } from "@/lib/use-reduced-motion";
import { cn } from "@/lib/utils";

/** Model confidence meter (uncalibrated [0,1]). */
export function ConfidenceBar({
  value,
  level,
  delay = 0,
}: {
  value: number; // 0..1
  level: "high" | "medium" | "low";
  delay?: number;
}) {
  const reduced = usePrefersReducedMotion();
  const tone =
    level === "high" ? "from-success to-cyan-400" : level === "medium" ? "from-warning to-accent-400" : "from-danger to-magenta-500";

  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between text-caption">
        <span className="text-ink-secondary">Model confidence</span>
        <span className={cn("font-medium capitalize", level === "high" ? "text-success-fg" : level === "medium" ? "text-warning-fg" : "text-danger-fg")}>
          {level} · {(value * 100).toFixed(0)}%
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-surface-overlay">
        <motion.div
          className={cn("h-full rounded-full bg-gradient-to-r", tone)}
          initial={{ width: reduced ? `${value * 100}%` : 0 }}
          animate={{ width: `${value * 100}%` }}
          transition={reduced ? { duration: 0 } : { duration: 0.9, ease: [0.16, 1, 0.3, 1], delay }}
        />
      </div>
    </div>
  );
}
