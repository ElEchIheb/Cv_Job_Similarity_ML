"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { Command, Search } from "lucide-react";
import { NAV } from "@/lib/nav";
import { api } from "@/lib/api/client";
import { ThemeToggle } from "./ThemeToggle";
import { CommandPalette } from "./CommandPalette";

export function TopBar({ userName }: { userName: string }) {
  const pathname = usePathname();
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [systemOk, setSystemOk] = useState(true);

  const current = NAV.find((n) => pathname?.startsWith(n.href));

  useEffect(() => {
    api.system().then(() => setSystemOk(true)).catch(() => setSystemOk(false));
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen(true);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const initials = userName.split(" ").map((s) => s[0]).slice(0, 2).join("").toUpperCase();

  return (
    <>
      <header className="sticky top-0 z-50 flex h-16 items-center gap-4 border-b border-subtle/10 glass px-5">
        <div className="flex items-center gap-2 text-body">
          <span className="text-ink-muted">NeuralHire</span>
          <span className="text-ink-muted">/</span>
          <span className="font-medium text-ink">{current?.label ?? "Overview"}</span>
        </div>

        <button
          onClick={() => setPaletteOpen(true)}
          className="ml-auto hidden items-center gap-2 rounded-lg border border-subtle/12 bg-surface-raised/60 px-3 py-2 text-caption text-ink-muted transition-colors hover:border-accent/30 hover:text-ink-secondary md:flex"
        >
          <Search className="h-4 w-4" />
          <span>Search…</span>
          <kbd className="ml-6 flex items-center gap-0.5 rounded bg-surface-overlay px-1.5 py-0.5 text-micro">
            <Command className="h-2.5 w-2.5" />K
          </kbd>
        </button>

        <div className="flex items-center gap-1.5 rounded-full border border-subtle/12 bg-surface-raised/60 px-2.5 py-1 text-caption">
          <span className="relative flex h-2 w-2">
            <motion.span
              className={`absolute inline-flex h-full w-full rounded-full ${systemOk ? "bg-success" : "bg-danger"}`}
              animate={{ opacity: [0.4, 1, 0.4] }}
              transition={{ duration: 2, repeat: Infinity }}
            />
            <span className={`relative inline-flex h-2 w-2 rounded-full ${systemOk ? "bg-success" : "bg-danger"}`} />
          </span>
          <span className="text-ink-secondary">{systemOk ? "All systems operational" : "Degraded"}</span>
        </div>

        <ThemeToggle />

        <button className="grid h-9 w-9 place-items-center rounded-full bg-[linear-gradient(120deg,#7c5cff,#22cfee)] text-caption font-semibold text-white shadow-e1">
          {initials}
        </button>
      </header>

      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
    </>
  );
}
