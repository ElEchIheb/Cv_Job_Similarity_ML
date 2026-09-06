"use client";

import { usePathname } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { pageTransition } from "@/lib/motion";

/** Route-change cross-fade + slight slide. */
export function PageTransition({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <AnimatePresence mode="wait">
      <motion.div key={pathname} variants={pageTransition} initial="hidden" animate="show" exit="exit">
        {children}
      </motion.div>
    </AnimatePresence>
  );
}
