"use client";

import { motion } from "framer-motion";
import { usePrefersReducedMotion } from "@/lib/use-reduced-motion";
import { cn } from "@/lib/utils";

/**
 * Animated SVG score ring. Draws from 0 → value over ~1.2s ease-out.
 * Serves as the accessible / reduced-motion fallback for the R3F score torus.
 */
export function ProgressRing({
  value,
  size = 220,
  stroke = 14,
  tone = "accent",
  children,
  className,
  delay = 0,
}: {
  value: number; // 0..100
  size?: number;
  stroke?: number;
  tone?: "accent" | "success" | "warning" | "danger";
  children?: React.ReactNode;
  className?: string;
  delay?: number;
}) {
  const reduced = usePrefersReducedMotion();
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - value / 100);
  const gradId = `ring-grad-${tone}`;

  const stops: Record<string, [string, string]> = {
    accent: ["#7c5cff", "#22cfee"],
    success: ["#2fd39a", "#3ee6ff"],
    warning: ["#f5b445", "#ff9a3c"],
    danger: ["#ec6a63", "#f65cc6"],
  };

  return (
    <div className={cn("relative inline-grid place-items-center", className)} style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90" aria-hidden>
        <defs>
          <linearGradient id={gradId} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={stops[tone][0]} />
            <stop offset="100%" stopColor={stops[tone][1]} />
          </linearGradient>
          <filter id={`glow-${tone}`}>
            <feGaussianBlur stdDeviation="4" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="rgb(var(--border-subtle) / 0.12)"
          strokeWidth={stroke}
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={`url(#${gradId})`}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          filter={`url(#glow-${tone})`}
          initial={{ strokeDashoffset: reduced ? offset : c }}
          animate={{ strokeDashoffset: offset }}
          transition={reduced ? { duration: 0 } : { duration: 1.2, ease: [0.16, 1, 0.3, 1], delay }}
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center">{children}</div>
    </div>
  );
}
