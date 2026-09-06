"use client";

import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";

const TONE_COLORS: Record<string, [string, string]> = {
  accent: ["#7c5cff", "#22cfee"],
  success: ["#2fd39a", "#3ee6ff"],
  warning: ["#f5b445", "#ff9a3c"],
  danger: ["#ec6a63", "#f65cc6"],
};

function Ring({ value, tone }: { value: number; tone: string }) {
  const arc = useRef<THREE.Mesh>(null);
  const grow = useRef(0);
  const target = Math.max(0.001, value / 100);
  const [c1, c2] = TONE_COLORS[tone] ?? TONE_COLORS.accent;

  const mat = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: new THREE.Color(c1),
        emissive: new THREE.Color(c2),
        emissiveIntensity: 0.5,
        metalness: 0.4,
        roughness: 0.25,
      }),
    [c1, c2],
  );

  useFrame((state, delta) => {
    grow.current = THREE.MathUtils.damp(grow.current, target, 3, delta);
    if (arc.current) {
      const g = arc.current.geometry as THREE.TorusGeometry;
      // rebuild arc geometry to reflect current fill
      arc.current.geometry.dispose();
      arc.current.geometry = new THREE.TorusGeometry(2, 0.34, 20, 120, grow.current * Math.PI * 2);
      arc.current.rotation.z = Math.PI / 2 + state.clock.elapsedTime * 0.12;
    }
  });

  return (
    <group rotation={[0.5, 0, 0]}>
      {/* dim full track */}
      <mesh rotation={[0, 0, Math.PI / 2]}>
        <torusGeometry args={[2, 0.16, 16, 120]} />
        <meshStandardMaterial color="#2a2b3f" roughness={0.8} metalness={0.1} />
      </mesh>
      {/* animated fill arc */}
      <mesh ref={arc} material={mat}>
        <torusGeometry args={[2, 0.34, 20, 120, 0.001]} />
      </mesh>
    </group>
  );
}

export default function ScoreTorus({ value, tone = "accent" }: { value: number; tone?: string }) {
  return (
    <Canvas camera={{ position: [0, 0, 6.2], fov: 50 }} dpr={[1, 1.5]} gl={{ alpha: true, antialias: true }}>
      <ambientLight intensity={0.6} />
      <pointLight position={[4, 4, 5]} intensity={2.2} color="#a99bff" />
      <pointLight position={[-4, -2, 3]} intensity={1.4} color="#22cfee" />
      <Ring value={value} tone={tone} />
    </Canvas>
  );
}
