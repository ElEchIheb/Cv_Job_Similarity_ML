"use client";

import { motion } from "framer-motion";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import { fadeUp } from "@/lib/motion";
import { cn } from "@/lib/utils";
import { CountUp } from "./CountUp";

/** Overview metric card — icon treatment, optional trend, hover lift. */
export function StatCard({
  label,
  value,
  suffix,
  decimals = 0,
  icon,
  trend,
  tone = "accent",
  className,
}: {
  label: string;
  value: number;
  suffix?: string;
  decimals?: number;
  icon: React.ReactNode;
  trend?: number; // +/- percentage
  tone?: "accent" | "success" | "warning" | "danger" | "cyan";
  className?: string;
}) {
  const toneRing: Record<string, string> = {
    accent: "text-accent-300 bg-accent/12",
    success: "text-success-fg bg-success-soft",
    warning: "text-warning-fg bg-warning-soft",
    danger: "text-danger-fg bg-danger-soft",
    cyan: "text-cyan-400 bg-cyan-500/12",
  };
  const up = (trend ?? 0) >= 0;

  return (
    <motion.div
      variants={fadeUp}
      whileHover={{ y: -4 }}
      transition={{ type: "spring", stiffness: 300, damping: 24 }}
      className={cn(
        "group relative overflow-hidden rounded-lg border border-subtle/12 bg-surface p-5 shadow-e2 transition-shadow hover:shadow-e4",
        className,
      )}
    >
      <div
        className="pointer-events-none absolute -right-8 -top-8 h-24 w-24 rounded-full opacity-0 blur-2xl transition-opacity duration-500 group-hover:opacity-100"
        style={{ background: "rgb(124 92 255 / 0.25)" }}
      />
      <div className="flex items-start justify-between">
        <span className={cn("grid h-10 w-10 place-items-center rounded-lg", toneRing[tone])}>{icon}</span>
        {typeof trend === "number" && (
          <span
            className={cn(
              "inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 text-caption font-medium",
              up ? "bg-success-soft text-success-fg" : "bg-danger-soft text-danger-fg",
            )}
          >
            {up ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
            {Math.abs(trend)}%
          </span>
        )}
      </div>
      <div className="mt-4">
        <div className="font-display text-h1 font-semibold text-ink">
          <CountUp to={value} decimals={decimals} suffix={suffix} />
        </div>
        <div className="mt-1 text-caption text-ink-secondary">{label}</div>
      </div>
    </motion.div>
  );
}
