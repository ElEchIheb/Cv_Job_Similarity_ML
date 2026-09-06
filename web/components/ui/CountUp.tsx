"use client";

import { useEffect, useRef, useState } from "react";
import { usePrefersReducedMotion } from "@/lib/use-reduced-motion";

/** Tabular-numeral count-up tied to a shared reveal timeline. */
export function CountUp({
  to,
  duration = 1200,
  decimals = 0,
  delay = 0,
  suffix = "",
  className,
}: {
  to: number;
  duration?: number;
  decimals?: number;
  delay?: number;
  suffix?: string;
  className?: string;
}) {
  const reduced = usePrefersReducedMotion();
  const [value, setValue] = useState(0);
  const raf = useRef<number>();

  useEffect(() => {
    if (reduced) {
      setValue(to);
      return;
    }
    let start: number | null = null;
    const startAt = performance.now() + delay;
    const tick = (now: number) => {
      if (now < startAt) {
        raf.current = requestAnimationFrame(tick);
        return;
      }
      if (start === null) start = now;
      const t = Math.min(1, (now - start) / duration);
      // easeOutExpo
      const eased = t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
      setValue(to * eased);
      if (t < 1) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => {
      if (raf.current) cancelAnimationFrame(raf.current);
    };
  }, [to, duration, delay, reduced]);

  return (
    <span className={className}>
      <span className="tnum">{value.toFixed(decimals)}</span>
      {suffix}
    </span>
  );
}
