"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { usePrefersReducedMotion } from "@/lib/use-reduced-motion";

type Cat = "matched" | "priority" | "missing" | "extra";

const CAT: Record<Cat, { color: string; label: string; ring: number; dashed: boolean; connected: boolean; phase: number }> = {
  matched: { color: "#2fd39a", label: "Matched", ring: 0.2, dashed: false, connected: true, phase: 0 },
  priority: { color: "#ec6a63", label: "Priority gap", ring: 0.34, dashed: true, connected: true, phase: 0.7 },
  missing: { color: "#f5b445", label: "Missing", ring: 0.34, dashed: true, connected: true, phase: 2.0 },
  extra: { color: "#7c5cff", label: "Additional", ring: 0.46, dashed: false, connected: false, phase: 0.35 },
};

interface Node {
  skill: string;
  cat: Cat;
  color: string;
  dashed: boolean;
  connected: boolean;
  x: number;
  y: number;
  dx: number;
  dy: number;
  dur: number;
}

/**
 * Skill constellation: required-role node at the centre, skills orbiting it.
 * Matched skills glow green + solid line; priority/missing glow red/amber + a
 * dashed (broken) line; additional skills float further out, unconnected.
 * Nodes drift gently and highlight (node + its edge + tooltip) on hover.
 * It is an SVG, so it *is* the reduced-motion/low-end fallback — under reduced
 * motion the drift is simply disabled and the layout is static.
 */
export function SkillConstellation({
  matched,
  priority,
  missing,
  extra,
  size = 380,
}: {
  matched: string[];
  priority: string[];
  missing: string[];
  extra: string[];
  size?: number;
}) {
  const reduced = usePrefersReducedMotion();
  const [hover, setHover] = useState<string | null>(null);
  const cx = size / 2;
  const cy = size / 2;

  const nodes = useMemo<Node[]>(() => {
    const groups: [Cat, string[]][] = [
      ["matched", matched.slice(0, 8)],
      ["priority", priority.slice(0, 6)],
      ["missing", missing.filter((m) => !priority.includes(m)).slice(0, 6)],
      ["extra", extra.slice(0, 6)],
    ];
    const out: Node[] = [];
    for (const [cat, arr] of groups) {
      const meta = CAT[cat];
      arr.forEach((skill, i) => {
        const ang = (i / Math.max(arr.length, 1)) * Math.PI * 2 + meta.phase;
        const r = meta.ring * size + (i % 2 ? 10 : -10);
        out.push({
          skill,
          cat,
          color: meta.color,
          dashed: meta.dashed,
          connected: meta.connected,
          x: cx + Math.cos(ang) * r,
          y: cy + Math.sin(ang) * r,
          dx: Math.cos(ang * 1.7) * 4,
          dy: Math.sin(ang * 2.1) * 4,
          dur: 3.5 + (i % 4) * 0.6,
        });
      });
    }
    return out;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [matched.join(), priority.join(), missing.join(), extra.join(), size]);

  const hovered = hover ? nodes.find((n) => n.skill === hover) : null;

  return (
    <div>
      <div className="relative mx-auto" style={{ width: size, height: size }} onMouseLeave={() => setHover(null)}>
        <svg width={size} height={size} role="img" aria-label="Skill constellation: candidate skills vs role requirements">
          {/* edges */}
          {nodes.filter((n) => n.connected).map((n) => (
            <line
              key={`e-${n.skill}`}
              x1={cx}
              y1={cy}
              x2={n.x}
              y2={n.y}
              stroke={n.color}
              strokeWidth={hover === n.skill ? 2 : 1}
              strokeDasharray={n.dashed ? "4 5" : undefined}
              strokeOpacity={hover && hover !== n.skill ? 0.12 : 0.45}
            />
          ))}
          {/* centre role node */}
          <circle cx={cx} cy={cy} r={22} fill="rgb(var(--bg-surface-raised))" stroke="rgb(124 92 255 / 0.6)" strokeWidth={2} />
          <text x={cx} y={cy} textAnchor="middle" dominantBaseline="central" className="fill-ink text-[10px] font-semibold">Role</text>
          {/* skill nodes */}
          {nodes.map((n) => {
            const active = hover === n.skill;
            const dim = hover && !active;
            return (
              <motion.g
                key={n.skill}
                animate={reduced ? {} : { x: [0, n.dx, 0], y: [0, n.dy, 0] }}
                transition={reduced ? {} : { duration: n.dur, repeat: Infinity, ease: "easeInOut" }}
                onMouseEnter={() => setHover(n.skill)}
                style={{ cursor: "pointer" }}
              >
                <circle
                  cx={n.x}
                  cy={n.y}
                  r={active ? 7 : 5}
                  fill={n.color}
                  opacity={dim ? 0.3 : 1}
                  style={{ filter: active ? `drop-shadow(0 0 7px ${n.color})` : `drop-shadow(0 0 3px ${n.color}99)` }}
                />
                <text
                  x={n.x}
                  y={n.y + (n.y > cy ? 15 : -11)}
                  textAnchor="middle"
                  className="fill-ink-secondary text-[9px] font-medium"
                  opacity={dim ? 0.25 : 1}
                >
                  {n.skill}
                </text>
              </motion.g>
            );
          })}
        </svg>
        {hovered && (
          <div
            className="pointer-events-none absolute z-10 -translate-x-1/2 -translate-y-full whitespace-nowrap rounded-md glass border border-subtle/15 px-2.5 py-1 text-caption shadow-e3"
            style={{ left: hovered.x, top: hovered.y - 6 }}
          >
            <span className="font-medium" style={{ color: hovered.color }}>{hovered.skill}</span>
            <span className="ml-1 text-ink-muted">· {CAT[hovered.cat].label}</span>
          </div>
        )}
      </div>
      <div className="mt-2 flex flex-wrap justify-center gap-4">
        {(Object.keys(CAT) as Cat[]).map((k) => (
          <span key={k} className="flex items-center gap-1.5 text-caption text-ink-secondary">
            <span className="h-2 w-2 rounded-full" style={{ background: CAT[k].color, boxShadow: `0 0 4px ${CAT[k].color}` }} />
            {CAT[k].label}
          </span>
        ))}
      </div>
    </div>
  );
}
