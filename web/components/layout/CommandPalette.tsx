"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { Search, CornerDownLeft } from "lucide-react";
import { NAV } from "@/lib/nav";
import { overlayScale } from "@/lib/motion";
import { cn } from "@/lib/utils";

export function CommandPalette({ open, onClose }: { open: boolean; onClose: () => void }) {
  const router = useRouter();
  const [q, setQ] = useState("");
  const [active, setActive] = useState(0);

  const results = useMemo(
    () => NAV.filter((n) => n.label.toLowerCase().includes(q.toLowerCase())),
    [q],
  );

  useEffect(() => {
    if (open) {
      setQ("");
      setActive(0);
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowDown") { e.preventDefault(); setActive((a) => Math.min(results.length - 1, a + 1)); }
      if (e.key === "ArrowUp") { e.preventDefault(); setActive((a) => Math.max(0, a - 1)); }
      if (e.key === "Enter" && results[active]) { router.push(results[active].href); onClose(); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, results, active, router, onClose]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-[120] flex items-start justify-center p-4 pt-[18vh]"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <div className="absolute inset-0 bg-canvas/50 backdrop-blur-glass" onClick={onClose} aria-hidden />
          <motion.div
            variants={overlayScale}
            initial="hidden"
            animate="show"
            exit="exit"
            className="relative z-10 w-full max-w-xl overflow-hidden rounded-xl border border-subtle/15 glass shadow-e5"
          >
            <div className="flex items-center gap-3 border-b border-subtle/10 px-4 py-3">
              <Search className="h-4.5 w-4.5 text-ink-muted" />
              <input
                autoFocus
                value={q}
                onChange={(e) => { setQ(e.target.value); setActive(0); }}
                placeholder="Search pages, candidates, jobs…"
                className="w-full bg-transparent text-body text-ink outline-none placeholder:text-ink-muted"
              />
              <kbd className="rounded bg-surface-overlay px-1.5 py-0.5 text-micro text-ink-muted">ESC</kbd>
            </div>
            <div className="max-h-80 overflow-y-auto p-2">
              {results.length === 0 && (
                <div className="px-3 py-8 text-center text-body text-ink-muted">No matches for “{q}”.</div>
              )}
              {results.map((r, i) => (
                <button
                  key={r.href}
                  onMouseEnter={() => setActive(i)}
                  onClick={() => { router.push(r.href); onClose(); }}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-body transition-colors",
                    i === active ? "bg-accent/12 text-ink" : "text-ink-secondary hover:bg-surface-raised/60",
                  )}
                >
                  <span className={cn("grid h-5 w-5 place-items-center", i === active && "text-accent-300")}>
                    {r.icon}
                  </span>
                  <span className="flex-1">{r.label}</span>
                  <span className="text-micro uppercase tracking-wide text-ink-muted">{r.section}</span>
                  {i === active && <CornerDownLeft className="h-3.5 w-3.5 text-ink-muted" />}
                </button>
              ))}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
