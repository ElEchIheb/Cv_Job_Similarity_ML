"use client";

import { motion } from "framer-motion";
import { usePrefersReducedMotion } from "@/lib/use-reduced-motion";
import { staggerContainer } from "@/lib/motion";
import type { ComponentScores } from "@/lib/api/types";

const ROWS: { key: keyof ComponentScores; label: string; grad: string }[] = [
  { key: "skill_score", label: "Skill match", grad: "from-accent-400 to-accent-600" },
  { key: "embedding_score", label: "Semantic relevance", grad: "from-cyan-400 to-cyan-600" },
  { key: "tfidf_score", label: "Keyword relevance", grad: "from-magenta-400 to-magenta-600" },
];

/** Animated component-score bars (Skills / Semantic / Keyword). */
export function ScoreBreakdown({ scores, delay = 0 }: { scores: ComponentScores; delay?: number }) {
  const reduced = usePrefersReducedMotion();
  return (
    <motion.div
      variants={staggerContainer(0.08, delay)}
      initial="hidden"
      animate="show"
      className="flex flex-col gap-4"
    >
      {ROWS.map((r) => {
        const raw = scores[r.key] ?? 0;
        const value = raw <= 1 ? raw * 100 : raw;
        return (
          <div key={r.key}>
            <div className="mb-1.5 flex items-center justify-between text-caption">
              <span className="text-ink-secondary">{r.label}</span>
              <span className="tnum font-medium text-ink">{value.toFixed(0)}%</span>
            </div>
            <div className="h-2.5 overflow-hidden rounded-full bg-surface-overlay">
              <motion.div
                className={`h-full rounded-full bg-gradient-to-r ${r.grad}`}
                initial={{ width: reduced ? `${value}%` : 0 }}
                whileInView={{ width: `${value}%` }}
                viewport={{ once: true }}
                transition={reduced ? { duration: 0 } : { duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
              />
            </div>
          </div>
        );
      })}
    </motion.div>
  );
}
