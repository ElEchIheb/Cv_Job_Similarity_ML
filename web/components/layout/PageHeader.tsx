"use client";

import { motion } from "framer-motion";

/** Cinematic page header — badge + gradient-highlighted title + subtitle. */
export function PageHeader({
  badge,
  title,
  highlight,
  subtitle,
}: {
  badge: string;
  title: string;
  highlight: string;
  subtitle: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 240, damping: 26 }}
      className="mb-6"
    >
      <div className="mb-2.5 inline-flex items-center gap-2 rounded-full border border-subtle/15 bg-surface-raised/60 px-3 py-1 text-micro font-semibold uppercase tracking-[0.14em] text-ink-secondary">
        <span className="h-1.5 w-1.5 rounded-full bg-accent-400 animate-pulse-glow" />
        {badge}
      </div>
      <h1 className="font-display text-h1 font-semibold text-ink">
        {title} <span className="text-gradient">{highlight}</span>
      </h1>
      <p className="mt-1.5 max-w-2xl text-body-lg text-ink-secondary">{subtitle}</p>
    </motion.div>
  );
}
