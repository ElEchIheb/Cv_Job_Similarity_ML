"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { usePrefersReducedMotion } from "@/lib/use-reduced-motion";
import { cn } from "@/lib/utils";

export interface RadarSeries {
  name: string;
  values: number[]; // 0..100, one per axis
  color: string;
  /** Dashed stroke for accessibility (distinguishable beyond hue). */
  dashed?: boolean;
}

/** Ease an array of numbers toward a target — powers draw-in + morph. */
function useAnimatedValues(target: number[], reduced: boolean, duration = 1000) {
  const [vals, setVals] = useState<number[]>(() => target.map(() => 0));
  const from = useRef<number[]>(target.map(() => 0));
  const raf = useRef<number>();

  useEffect(() => {
    if (reduced) {
      setVals(target);
      from.current = target;
      return;
    }
    const start = performance.now();
    const startVals = from.current.length === target.length ? from.current : target.map(() => 0);
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      const next = target.map((v, i) => startVals[i] + (v - startVals[i]) * eased);
      setVals(next);
      if (t < 1) raf.current = requestAnimationFrame(tick);
      else from.current = target;
    };
    raf.current = requestAnimationFrame(tick);
    return () => {
      if (raf.current) cancelAnimationFrame(raf.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(target), reduced]);

  return vals;
}

export function RadarChart({
  labels,
  series,
  size = 340,
  className,
}: {
  labels: string[];
  series: RadarSeries[];
  size?: number;
  className?: string;
}) {
  const reduced = usePrefersReducedMotion();
  const [hover, setHover] = useState<{ axis: number; s: number } | null>(null);
  const cx = size / 2;
  const cy = size / 2;
  const radius = size / 2 - 46;
  const n = labels.length;
  const angle = (i: number) => (Math.PI * 2 * i) / n - Math.PI / 2;
  const point = (val: number, i: number) => {
    const rr = (val / 100) * radius;
    return [cx + rr * Math.cos(angle(i)), cy + rr * Math.sin(angle(i))] as const;
  };

  // Animate each series independently.
  const animated = series.map((s) => useAnimatedValues(s.values, reduced)); // eslint-disable-line react-hooks/rules-of-hooks
  const poly = (vals: number[]) => vals.map((v, i) => point(v, i).join(",")).join(" ");

  const rings = [0.25, 0.5, 0.75, 1];

  return (
    <div className={cn("relative inline-block", className)}>
      <svg width={size} height={size} role="img" aria-label="Competency radar: candidate vs required">
        {/* grid rings */}
        {rings.map((r) => (
          <polygon
            key={r}
            points={labels.map((_, i) => point(r * 100, i).join(",")).join(" ")}
            fill="none"
            stroke="rgb(var(--border-subtle) / 0.1)"
            strokeWidth={1}
          />
        ))}
        {/* axes + labels */}
        {labels.map((label, i) => {
          const [x, y] = point(112, i);
          const [ax, ay] = point(100, i);
          return (
            <g key={label}>
              <line x1={cx} y1={cy} x2={ax} y2={ay} stroke="rgb(var(--border-subtle) / 0.12)" strokeWidth={1} />
              <text
                x={x}
                y={y}
                textAnchor={Math.abs(x - cx) < 8 ? "middle" : x > cx ? "start" : "end"}
                dominantBaseline="middle"
                className="fill-ink-secondary text-[11px] font-medium"
              >
                {label}
              </text>
            </g>
          );
        })}
        {/* series polygons */}
        {series.map((s, si) => (
          <motion.polygon
            key={s.name}
            points={poly(animated[si])}
            fill={s.color}
            fillOpacity={0.12}
            stroke={s.color}
            strokeWidth={2}
            strokeDasharray={s.dashed ? "5 4" : undefined}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.4, delay: si * 0.15 }}
          />
        ))}
        {/* vertices (hover targets) */}
        {series.map((s, si) =>
          animated[si].map((v, i) => {
            const [x, y] = point(v, i);
            return (
              <circle
                key={`${s.name}-${i}`}
                cx={x}
                cy={y}
                r={hover?.axis === i && hover?.s === si ? 6 : 4}
                fill={s.color}
                stroke="rgb(var(--bg-surface))"
                strokeWidth={2}
                className="cursor-pointer transition-all"
                onMouseEnter={() => setHover({ axis: i, s: si })}
                onMouseLeave={() => setHover(null)}
              />
            );
          }),
        )}
      </svg>

      <AnimatePresence>
        {hover && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ type: "spring", stiffness: 400, damping: 24 }}
            className="pointer-events-none absolute z-10 -translate-x-1/2 -translate-y-full rounded-md glass border border-subtle/15 px-2.5 py-1.5 text-caption shadow-e3"
            style={{
              left: point(series[hover.s].values[hover.axis], hover.axis)[0],
              top: point(series[hover.s].values[hover.axis], hover.axis)[1] - 8,
            }}
          >
            <div className="font-medium text-ink">{labels[hover.axis]}</div>
            <div className="tnum" style={{ color: series[hover.s].color }}>
              {series[hover.s].name}: {series[hover.s].values[hover.axis].toFixed(0)}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* legend */}
      <div className="mt-2 flex items-center justify-center gap-5">
        {series.map((s) => (
          <div key={s.name} className="flex items-center gap-2 text-caption text-ink-secondary">
            <span
              className="inline-block h-0 w-5 border-t-2"
              style={{ borderColor: s.color, borderStyle: s.dashed ? "dashed" : "solid" }}
            />
            {s.name}
          </div>
        ))}
      </div>
    </div>
  );
}
