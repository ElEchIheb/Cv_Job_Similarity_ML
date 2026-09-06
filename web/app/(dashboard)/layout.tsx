"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, getToken } from "@/lib/api/client";
import type { User } from "@/lib/api/types";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopBar } from "@/components/layout/TopBar";
import { PageTransition } from "@/components/layout/PageTransition";
import { Logo } from "@/components/layout/Logo";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    api
      .me()
      .then((u) => setUser(u))
      .catch(() => router.replace("/login"))
      .finally(() => setReady(true));
  }, [router]);

  const signOut = () => {
    api.logout();
    router.replace("/login");
  };

  if (!ready || !user) {
    return (
      <div className="grid min-h-screen place-items-center bg-canvas">
        <div className="animate-pulse">
          <Logo />
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-canvas">
      <Sidebar onSignOut={signOut} />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar userName={user.full_name} />
        <main className="mx-auto w-full max-w-container flex-1 px-5 py-7 md:px-7">
          <PageTransition>{children}</PageTransition>
        </main>
      </div>
    </div>
  );
}
