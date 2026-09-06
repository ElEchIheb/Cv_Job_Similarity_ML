"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

/**
 * Sidebar nav item. The active indicator uses a shared layoutId so it slides
 * smoothly between items on navigation.
 */
export function NavItem({
  href,
  icon,
  label,
  active,
  collapsed,
}: {
  href: string;
  icon: React.ReactNode;
  label: string;
  active: boolean;
  collapsed?: boolean;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-body transition-colors",
        active ? "text-ink" : "text-ink-secondary hover:text-ink hover:bg-surface-raised/50",
      )}
    >
      {active && (
        <motion.span
          layoutId="nav-active"
          transition={{ type: "spring", stiffness: 380, damping: 32 }}
          className="absolute inset-0 rounded-lg bg-accent/12 ring-1 ring-accent/25"
        />
      )}
      <span className={cn("relative z-10 grid h-5 w-5 place-items-center", active && "text-accent-300")}>
        {icon}
      </span>
      {!collapsed && <span className="relative z-10 truncate font-medium">{label}</span>}
      {active && !collapsed && (
        <motion.span
          layoutId="nav-dot"
          className="relative z-10 ml-auto h-1.5 w-1.5 rounded-full bg-accent-400"
        />
      )}
    </Link>
  );
}
