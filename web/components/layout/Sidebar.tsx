"use client";

import { usePathname } from "next/navigation";
import { LogOut } from "lucide-react";
import { motion } from "framer-motion";
import { NAV, NAV_SECTIONS } from "@/lib/nav";
import { NavItem } from "@/components/ui/NavItem";
import { Logo } from "./Logo";

export function Sidebar({ onSignOut }: { onSignOut?: () => void }) {
  const pathname = usePathname();

  return (
    <aside className="sticky top-0 hidden h-screen w-[260px] shrink-0 flex-col border-r border-subtle/10 bg-surface/40 px-4 py-5 lg:flex">
      <div className="px-2">
        <Logo />
      </div>

      <nav className="mt-7 flex flex-1 flex-col gap-5 overflow-y-auto">
        {NAV_SECTIONS.map((section) => {
          const items = NAV.filter((n) => n.section === section);
          if (!items.length) return null;
          return (
            <div key={section}>
              <div className="mb-1.5 px-3 text-micro font-semibold uppercase tracking-[0.14em] text-ink-muted">
                {section}
              </div>
              <div className="flex flex-col gap-0.5">
                {items.map((item) => (
                  <div key={item.href} className="relative">
                    <NavItem
                      href={item.href}
                      icon={item.icon}
                      label={item.label}
                      active={pathname === item.href || (pathname?.startsWith(item.href + "/") ?? false)}
                    />
                    {!item.ready && (
                      <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 rounded-full bg-surface-overlay px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wide text-ink-muted">
                        soon
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </nav>

      <motion.button
        onClick={onSignOut}
        whileHover={{ x: 2 }}
        className="mt-4 flex items-center gap-3 rounded-lg px-3 py-2.5 text-body text-ink-secondary transition-colors hover:bg-danger-soft hover:text-danger-fg"
      >
        <LogOut className="h-4.5 w-4.5" />
        Sign out
      </motion.button>
    </aside>
  );
}
