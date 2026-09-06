"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/api/client";
import { Logo } from "@/components/layout/Logo";

export default function Home() {
  const router = useRouter();
  useEffect(() => {
    router.replace(getToken() ? "/overview" : "/login");
  }, [router]);

  return (
    <div className="grid min-h-screen place-items-center bg-canvas">
      <div className="animate-pulse">
        <Logo />
      </div>
    </div>
  );
}
