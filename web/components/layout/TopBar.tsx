"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
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
      <header className="relative z-50 flex min-h-16 flex-wrap items-center gap-3 border-b border-subtle/10 glass px-4 py-2 lg:sticky lg:top-0 lg:h-16 lg:flex-nowrap lg:px-5 lg:py-0">
        <div className="flex min-w-0 items-center gap-2 text-body">
          <span className="text-ink-muted">JobTest</span>
          <span className="text-ink-muted">/</span>
          <span className="truncate font-medium text-ink">{current?.label ?? "Overview"}</span>
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

        <div className="flex shrink-0 items-center gap-1.5 rounded-full border border-subtle/12 bg-surface-raised/60 px-2.5 py-1 text-caption">
          <span className="relative flex h-2 w-2">
            <motion.span
              className={`absolute inline-flex h-full w-full rounded-full ${systemOk ? "bg-success" : "bg-danger"}`}
              animate={{ opacity: [0.4, 1, 0.4] }}
              transition={{ duration: 2, repeat: Infinity }}
            />
            <span className={`relative inline-flex h-2 w-2 rounded-full ${systemOk ? "bg-success" : "bg-danger"}`} />
          </span>
          <span className="text-ink-secondary">
            <span className="sm:hidden">{systemOk ? "Online" : "Issue"}</span>
            <span className="hidden sm:inline">{systemOk ? "All systems operational" : "Degraded"}</span>
          </span>
        </div>

        <ThemeToggle />

        <button className="grid h-9 w-9 place-items-center rounded-full bg-[linear-gradient(120deg,#7c5cff,#22cfee)] text-caption font-semibold text-white shadow-e1">
          {initials}
        </button>

        <nav className="order-last -mx-1 flex w-full gap-1 overflow-x-auto pb-0.5 lg:hidden" aria-label="Main navigation">
          {NAV.map((item) => {
            const active = pathname === item.href || (pathname?.startsWith(item.href + "/") ?? false);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`flex shrink-0 items-center gap-1.5 rounded-lg px-2.5 py-2 text-caption font-medium transition-colors ${
                  active ? "bg-accent/15 text-accent-300 ring-1 ring-accent/25" : "text-ink-secondary hover:bg-surface-raised/60 hover:text-ink"
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </header>

      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
    </>
  );
}
