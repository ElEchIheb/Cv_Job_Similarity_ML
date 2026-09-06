"use client";

import { useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";
import { overlayScale } from "@/lib/motion";
import { cn } from "@/lib/utils";

/** Blur-backdrop modal with a spring entrance/exit. */
export function Modal({
  open,
  onClose,
  title,
  children,
  className,
}: {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  className?: string;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-[100] flex items-center justify-center p-5"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <div
            className="absolute inset-0 bg-canvas/60 backdrop-blur-glass"
            onClick={onClose}
            aria-hidden
          />
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-label={title}
            variants={overlayScale}
            initial="hidden"
            animate="show"
            exit="exit"
            className={cn(
              "relative z-10 w-full max-w-lg rounded-xl border border-subtle/15 bg-surface-raised shadow-e5",
              className,
            )}
          >
            {title && (
              <div className="flex items-center justify-between border-b border-subtle/10 p-5">
                <h2 className="font-display text-h4 font-semibold text-ink">{title}</h2>
                <button
                  onClick={onClose}
                  className="rounded-md p-1 text-ink-muted hover:bg-surface-overlay hover:text-ink"
                  aria-label="Close"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            )}
            <div className="p-5">{children}</div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
