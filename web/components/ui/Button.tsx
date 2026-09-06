"use client";

import { forwardRef } from "react";
import { motion, type HTMLMotionProps } from "framer-motion";
import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "ghost" | "danger" | "outline";
type Size = "sm" | "md" | "lg";

interface ButtonProps extends Omit<HTMLMotionProps<"button">, "ref"> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  icon?: React.ReactNode;
}

const sizes: Record<Size, string> = {
  sm: "h-8 px-3 text-caption gap-1.5 rounded-md",
  md: "h-10 px-4 text-body gap-2 rounded-lg",
  lg: "h-12 px-6 text-body-lg gap-2 rounded-lg",
};

const variants: Record<Variant, string> = {
  primary:
    "text-white bg-[linear-gradient(120deg,#7c5cff_0%,#6a3ff2_50%,#f65cc6_140%)] bg-[length:180%_100%] bg-left hover:bg-right shadow-e2 hover:shadow-glow-accent transition-[background-position,box-shadow,transform]",
  secondary:
    "text-ink bg-surface-raised border border-subtle/15 hover:border-accent/40 hover:bg-surface-overlay shadow-e1",
  outline:
    "text-ink bg-transparent border border-subtle/20 hover:border-accent/50 hover:bg-surface/60",
  ghost: "text-ink-secondary hover:text-ink hover:bg-surface-raised/70",
  danger: "text-white bg-danger hover:brightness-110 shadow-e1 hover:shadow-glow-danger",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "primary", size = "md", loading, icon, className, children, disabled, ...props },
  ref,
) {
  return (
    <motion.button
      ref={ref}
      whileHover={disabled || loading ? undefined : { scale: 1.02 }}
      whileTap={disabled || loading ? undefined : { scale: 0.97 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
      disabled={disabled || loading}
      className={cn(
        "relative inline-flex items-center justify-center overflow-hidden font-medium select-none",
        "disabled:opacity-50 disabled:pointer-events-none",
        sizes[size],
        variants[variant],
        className,
      )}
      {...props}
    >
      {loading && (
        <span className="absolute inset-0 -translate-x-full animate-shimmer bg-[linear-gradient(90deg,transparent,rgba(255,255,255,0.22),transparent)]" />
      )}
      {loading ? (
        <span className="inline-flex items-center gap-2">
          <Spinner />
          <span>Working…</span>
        </span>
      ) : (
        <>
          {icon}
          {children}
        </>
      )}
    </motion.button>
  );
});

function Spinner() {
  return (
    <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden>
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeOpacity="0.25" strokeWidth="3" />
      <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}
