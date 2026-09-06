"use client";

import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

/**
 * Lightweight neural-network motif: a slow-drifting field of nodes with
 * connecting edges near each other. Low poly count, no textures, one draw group
 * rotating — designed to hold 60fps on mid-range laptops. Rendered only when
 * motion is allowed (the wrapper swaps in a static gradient otherwise).
 */
function Field({ count = 90, accent }: { count?: number; accent: THREE.Color }) {
  const group = useRef<THREE.Group>(null);

  const { positions, linePositions } = useMemo(() => {
    const pts: THREE.Vector3[] = [];
    for (let i = 0; i < count; i++) {
      pts.push(
        new THREE.Vector3(
          (Math.random() - 0.5) * 14,
          (Math.random() - 0.5) * 8,
          (Math.random() - 0.5) * 6,
        ),
      );
    }
    const positions = new Float32Array(count * 3);
    pts.forEach((p, i) => {
      positions[i * 3] = p.x;
      positions[i * 3 + 1] = p.y;
      positions[i * 3 + 2] = p.z;
    });

    // Connect nearby nodes (capped for cheapness).
    const lines: number[] = [];
    const maxDist = 2.4;
    let edges = 0;
    for (let i = 0; i < count && edges < 160; i++) {
      for (let j = i + 1; j < count && edges < 160; j++) {
        if (pts[i].distanceTo(pts[j]) < maxDist) {
          lines.push(pts[i].x, pts[i].y, pts[i].z, pts[j].x, pts[j].y, pts[j].z);
          edges++;
        }
      }
    }
    return { positions, linePositions: new Float32Array(lines) };
  }, [count]);

  useFrame((state, delta) => {
    if (!group.current) return;
    group.current.rotation.y += delta * 0.04;
    group.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.1) * 0.06;
  });

  return (
    <group ref={group}>
      <points>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[positions, 3]} />
        </bufferGeometry>
        <pointsMaterial
          size={0.09}
          color={accent}
          transparent
          opacity={0.9}
          sizeAttenuation
          depthWrite={false}
        />
      </points>
      <lineSegments>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[linePositions, 3]} />
        </bufferGeometry>
        <lineBasicMaterial color={accent} transparent opacity={0.14} depthWrite={false} />
      </lineSegments>
    </group>
  );
}

export default function NeuralField({ intensity = 1 }: { intensity?: number }) {
  const accent = useMemo(() => new THREE.Color("#7c5cff"), []);
  return (
    <Canvas
      camera={{ position: [0, 0, 9], fov: 60 }}
      dpr={[1, 1.5]}
      gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
      style={{ pointerEvents: "none" }}
    >
      <fog attach="fog" args={["#090a12", 6, 18]} />
      <Field accent={accent} count={Math.round(90 * intensity)} />
    </Canvas>
  );
}
