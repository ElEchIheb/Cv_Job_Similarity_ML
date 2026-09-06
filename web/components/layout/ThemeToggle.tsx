"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "@/lib/theme";

/** Theme toggle — the whole surface cross-fades via the body transition. */
export function ThemeToggle() {
  const { theme, toggle } = useTheme();
  const dark = theme === "dark";
  return (
    <button
      onClick={toggle}
      aria-label={`Switch to ${dark ? "light" : "dark"} theme`}
      className="relative grid h-9 w-9 place-items-center overflow-hidden rounded-lg border border-subtle/12 bg-surface-raised text-ink-secondary transition-colors hover:text-ink hover:border-accent/30"
    >
      <AnimatePresence mode="wait" initial={false}>
        <motion.span
          key={theme}
          initial={{ y: 14, opacity: 0, rotate: -30 }}
          animate={{ y: 0, opacity: 1, rotate: 0 }}
          exit={{ y: -14, opacity: 0, rotate: 30 }}
          transition={{ type: "spring", stiffness: 300, damping: 24 }}
        >
          {dark ? <Moon className="h-4.5 w-4.5" /> : <Sun className="h-4.5 w-4.5" />}
        </motion.span>
      </AnimatePresence>
    </button>
  );
}
