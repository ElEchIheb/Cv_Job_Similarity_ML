"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion, MotionConfig } from "framer-motion";
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
            <MotionConfig reducedMotion="user">
              <motion.div layout className="max-h-80 overflow-y-auto p-2">
                {results.length === 0 && (
                  <div className="px-3 py-8 text-center text-body text-ink-muted">No matches for “{q}”.</div>
                )}
                <AnimatePresence mode="popLayout" initial={false}>
                  {results.map((r, i) => (
                    <motion.button
                      key={r.href}
                      layout
                      initial={{ opacity: 0, y: 4 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.96 }}
                      transition={{ type: "spring", stiffness: 500, damping: 40 }}
                      onMouseEnter={() => setActive(i)}
                      onClick={() => { router.push(r.href); onClose(); }}
                      className="relative flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-body"
                    >
                      {i === active && (
                        <motion.span
                          layoutId="cmd-active"
                          transition={{ type: "spring", stiffness: 520, damping: 38 }}
                          className="absolute inset-0 rounded-lg bg-accent/12 ring-1 ring-accent/20"
                        />
                      )}
                      <motion.span
                        animate={{ scale: i === active ? 1.12 : 1 }}
                        transition={{ type: "spring", stiffness: 400, damping: 22 }}
                        className={cn("relative z-10 grid h-5 w-5 place-items-center", i === active ? "text-accent-300" : "text-ink-secondary")}
                      >
                        {r.icon}
                      </motion.span>
                      <span className={cn("relative z-10 flex-1", i === active ? "text-ink" : "text-ink-secondary")}>{r.label}</span>
                      <span className="relative z-10 text-micro uppercase tracking-wide text-ink-muted">{r.section}</span>
                      {i === active && (
                        <motion.span initial={{ opacity: 0, x: -4 }} animate={{ opacity: 1, x: 0 }} className="relative z-10">
                          <CornerDownLeft className="h-3.5 w-3.5 text-ink-muted" />
                        </motion.span>
                      )}
                    </motion.button>
                  ))}
                </AnimatePresence>
              </motion.div>
            </MotionConfig>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
