"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";
import { usePrefersReducedMotion } from "@/lib/use-reduced-motion";
import { cn } from "@/lib/utils";

const NeuralField = dynamic(() => import("./NeuralField"), { ssr: false });

/**
 * Ambient 3D backdrop for Login + Overview hero.
 * Degrades gracefully: a static gradient mesh renders immediately (and stays
 * for reduced-motion or low-end devices); the WebGL field mounts over it only
 * when motion is allowed and the device isn't obviously low-powered.
 */
export function AmbientBackground({
  intensity = 1,
  parallax = false,
  className,
}: {
  intensity?: number;
  parallax?: boolean;
  className?: string;
}) {
  const reduced = usePrefersReducedMotion();
  const [allow3d, setAllow3d] = useState(false);
  const pointer = useRef({ x: 0, y: 0 });

  useEffect(() => {
    if (reduced) {
      setAllow3d(false);
      return;
    }
    // crude low-end guard: few cores → skip WebGL
    const cores = navigator.hardwareConcurrency ?? 4;
    setAllow3d(cores >= 4);
  }, [reduced]);

  useEffect(() => {
    if (!parallax || reduced) return;
    const onMove = (e: MouseEvent) => {
      pointer.current.x = (e.clientX / window.innerWidth) * 2 - 1;
      pointer.current.y = (e.clientY / window.innerHeight) * 2 - 1;
    };
    window.addEventListener("mousemove", onMove);
    return () => window.removeEventListener("mousemove", onMove);
  }, [parallax, reduced]);

  return (
    <div className={cn("pointer-events-none absolute inset-0 overflow-hidden", className)} aria-hidden>
      {/* Static gradient-mesh fallback — always present underneath */}
      <div className="absolute inset-0">
        <div
          className="absolute -left-1/4 top-[-10%] h-[60vh] w-[60vh] rounded-full blur-[120px]"
          style={{ background: "rgb(124 92 255 / 0.28)" }}
        />
        <div
          className="absolute right-[-10%] top-1/4 h-[50vh] w-[50vh] rounded-full blur-[120px]"
          style={{ background: "rgb(34 207 238 / 0.18)" }}
        />
        <div
          className="absolute bottom-[-15%] left-1/3 h-[55vh] w-[55vh] rounded-full blur-[130px]"
          style={{ background: "rgb(246 92 198 / 0.16)" }}
        />
      </div>
      {allow3d && (
        <div className="absolute inset-0">
          <NeuralField intensity={intensity} pointer={parallax ? pointer : null} />
        </div>
      )}
    </div>
  );
}
