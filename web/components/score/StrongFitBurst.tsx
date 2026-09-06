"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { usePrefersReducedMotion } from "@/lib/use-reduced-motion";
import { cn } from "@/lib/utils";

/**
 * A brief (~0.9s), restrained premium burst for the Strong Fit / HIRE verdict:
 * a soft radial light flare, one expanding ring, and a few drifting particles in
 * the success→cyan accent gradient. Sits behind the score/verdict (pointer-events
 * none, doesn't obscure text). Skipped entirely under reduced-motion — the
 * existing verdict glow-pulse carries the moment there instead.
 */
export function StrongFitBurst({ show, size = "md" }: { show: boolean; size?: "sm" | "md" }) {
  const reduced = usePrefersReducedMotion();
  const particles = useMemo(
    () =>
      Array.from({ length: size === "sm" ? 6 : 9 }).map((_, i, arr) => ({
        angle: (i / arr.length) * Math.PI * 2 + (i % 2 ? 0.4 : 0),
        dist: (size === "sm" ? 46 : 74) + Math.random() * 26,
        dur: 0.7 + Math.random() * 0.3,
        cyan: i % 2 === 0,
      })),
    [size],
  );

  if (!show || reduced) return null;
  const flare = size === "sm" ? "h-28 w-28" : "h-40 w-40";
  const ring = size === "sm" ? "h-20 w-20" : "h-28 w-28";

  return (
    <div className="pointer-events-none absolute inset-0 z-0 grid place-items-center overflow-visible" aria-hidden>
      <motion.div
        initial={{ scale: 0.4, opacity: 0 }}
        animate={{ scale: [0.4, 1.5, 2.1], opacity: [0, 0.5, 0] }}
        transition={{ duration: 0.9, ease: "easeOut", times: [0, 0.35, 1] }}
        className={cn("absolute rounded-full blur-2xl", flare)}
        style={{ background: "radial-gradient(circle, rgba(47,211,154,0.55), rgba(34,207,238,0.22) 45%, transparent 70%)" }}
      />
      <motion.div
        initial={{ scale: 0.6, opacity: 0.55 }}
        animate={{ scale: 1.9, opacity: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className={cn("absolute rounded-full border border-success/60", ring)}
      />
      {particles.map((p, i) => (
        <motion.span
          key={i}
          initial={{ x: 0, y: 0, opacity: 0, scale: 0.5 }}
          animate={{
            x: Math.cos(p.angle) * p.dist,
            y: Math.sin(p.angle) * p.dist,
            opacity: [0, 1, 0],
            scale: [0.5, 1, 0.3],
          }}
          transition={{ duration: p.dur, ease: "easeOut", delay: 0.05 }}
          className="absolute h-1.5 w-1.5 rounded-full"
          style={{ background: p.cyan ? "#22cfee" : "#2fd39a", boxShadow: "0 0 6px currentColor" }}
        />
      ))}
    </div>
  );
}
