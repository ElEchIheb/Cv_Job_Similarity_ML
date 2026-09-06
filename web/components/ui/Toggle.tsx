"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

/** Accessible on/off switch with a spring-driven knob. */
export function Toggle({
  checked,
  onChange,
  label,
  className,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label?: string;
  className?: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={cn(
        "relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
        checked ? "bg-accent" : "bg-surface-overlay ring-1 ring-subtle/20",
        className,
      )}
    >
      <motion.span
        layout
        transition={{ type: "spring", stiffness: 500, damping: 32 }}
        className={cn(
          "block h-4 w-4 rounded-full bg-white shadow-e1",
          checked ? "ml-6" : "ml-1",
        )}
      />
    </button>
  );
}
