"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { usePrefersReducedMotion } from "@/lib/use-reduced-motion";
import { CountUp } from "@/components/ui/CountUp";
import { DECISION_STATUS } from "@/lib/utils";
import type { Decision } from "@/lib/api/types";
import { ScoreObject } from "./ScoreObject";
import { VerdictBadge } from "./VerdictBadge";
import { ConfidenceBar } from "./ConfidenceBar";
import { StrongFitBurst } from "./StrongFitBurst";

/**
 * The emotional climax: score object fills 0→value (~1.2s), the numeral counts
 * up on the same timeline, and the verdict badge scale-ins with a glow only once
 * the count finishes — a "verdict is in" beat.
 */
export function ScoreReveal({
  percentage,
  decision,
  confidence,
  confidenceLevel,
}: {
  percentage: number;
  decision: Decision;
  confidence: number;
  confidenceLevel: "high" | "medium" | "low";
}) {
  const reduced = usePrefersReducedMotion();
  const tone = DECISION_STATUS[decision];
  const [verdictIn, setVerdictIn] = useState(reduced);

  useEffect(() => {
    if (reduced) return setVerdictIn(true);
    const t = setTimeout(() => setVerdictIn(true), 1250);
    return () => clearTimeout(t);
  }, [reduced]);

  return (
    <div className="flex flex-col items-center gap-5">
      <div className="relative grid place-items-center">
        <StrongFitBurst show={decision === "HIRE" && verdictIn} />
        <ScoreObject value={percentage} tone={tone} size={248}>
          <div className="flex flex-col items-center">
            <div className="font-display text-[3.5rem] font-bold leading-none">
              <CountUp to={percentage} decimals={0} duration={1200} className="text-gradient" />
              <span className="text-gradient text-h2 align-top">%</span>
            </div>
            <span className="mt-1 text-caption uppercase tracking-widest text-ink-muted">Compatibility</span>
          </div>
        </ScoreObject>
      </div>

      <div className="h-10">
        <AnimatePresence>
          {verdictIn && (
            <motion.div key="verdict" exit={{ opacity: 0 }}>
              <VerdictBadge decision={decision} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="w-full max-w-xs">
        <ConfidenceBar value={confidence} level={confidenceLevel} delay={reduced ? 0 : 1.3} />
      </div>
    </div>
  );
}
