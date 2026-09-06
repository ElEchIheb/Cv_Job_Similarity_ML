"use client";

import { motion } from "framer-motion";
import { CheckCircle2, MinusCircle, XCircle } from "lucide-react";
import { verdictReveal } from "@/lib/motion";
import { BAND_LABEL, DECISION_STATUS, cn } from "@/lib/utils";
import type { Decision } from "@/lib/api/types";

const ICONS = { HIRE: CheckCircle2, CONSIDER: MinusCircle, REJECT: XCircle };
const GLOW = {
  success: "shadow-glow-success",
  warning: "shadow-glow-warning",
  danger: "shadow-glow-danger",
} as const;
const TONE = {
  success: "bg-success-soft text-success-fg ring-success/40",
  warning: "bg-warning-soft text-warning-fg ring-warning/40",
  danger: "bg-danger-soft text-danger-fg ring-danger/40",
} as const;

/** "The verdict is in" badge — scale-ins with a one-time glow pulse. */
export function VerdictBadge({ decision, animate = true }: { decision: Decision; animate?: boolean }) {
  const status = DECISION_STATUS[decision];
  const Icon = ICONS[decision];
  return (
    <motion.div
      variants={animate ? verdictReveal : undefined}
      initial={animate ? "hidden" : false}
      animate="show"
      className={cn(
        "inline-flex items-center gap-2 rounded-full px-4 py-2 text-body-lg font-semibold ring-1",
        TONE[status],
        GLOW[status],
      )}
    >
      <Icon className="h-5 w-5" />
      {BAND_LABEL[decision]}
    </motion.div>
  );
}
