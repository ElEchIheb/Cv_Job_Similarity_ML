"use client";

import { ThemeProvider } from "@/lib/theme";
import { ToastProvider } from "@/components/ui/Toast";
import { DecisionConfigProvider } from "@/lib/decision-config";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <DecisionConfigProvider>
        <ToastProvider>{children}</ToastProvider>
      </DecisionConfigProvider>
    </ThemeProvider>
  );
}
