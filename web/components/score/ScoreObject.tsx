"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { usePrefersReducedMotion } from "@/lib/use-reduced-motion";
import { ProgressRing } from "@/components/ui/ProgressRing";

const ScoreTorus = dynamic(() => import("@/components/three/ScoreTorus"), { ssr: false });

/**
 * The compatibility score object. Renders a slow-rotating 3D torus that fills to
 * the score; falls back to the animated SVG ProgressRing for reduced-motion /
 * low-end devices. Center content (numerals, verdict) is overlaid by the parent.
 */
export function ScoreObject({
  value,
  tone = "accent",
  size = 240,
  children,
}: {
  value: number;
  tone?: "accent" | "success" | "warning" | "danger";
  size?: number;
  children?: React.ReactNode;
}) {
  const reduced = usePrefersReducedMotion();
  const [use3d, setUse3d] = useState(false);

  useEffect(() => {
    if (reduced) return setUse3d(false);
    const cores = navigator.hardwareConcurrency ?? 4;
    setUse3d(cores >= 4);
  }, [reduced]);

  return (
    <div className="relative grid place-items-center" style={{ width: size, height: size }}>
      {use3d ? (
        <>
          <div className="absolute inset-0">
            <ScoreTorus value={value} tone={tone} />
          </div>
          <div className="absolute inset-0 grid place-items-center">{children}</div>
        </>
      ) : (
        <ProgressRing value={value} tone={tone} size={size} stroke={16}>
          {children}
        </ProgressRing>
      )}
    </div>
  );
}
