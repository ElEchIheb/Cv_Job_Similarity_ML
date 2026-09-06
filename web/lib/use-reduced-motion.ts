"use client";

import { useEffect, useState } from "react";

/**
 * Reactive prefers-reduced-motion hook. Every animated surface consults this to
 * provide an instant/static fallback (and the 3D scene disables entirely).
 * Returns false during SSR / first paint to avoid hydration mismatch, then syncs.
 */
export function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mq.matches);
    const onChange = (e: MediaQueryListEvent) => setReduced(e.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  return reduced;
}
