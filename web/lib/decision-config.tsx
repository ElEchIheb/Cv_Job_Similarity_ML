"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { DEFAULT_POTENTIAL_FIT, DEFAULT_STRONG_FIT } from "./constants";

/**
 * Active decision thresholds — the Next.js equivalent of frontend/decision_state.py.
 * Settings writes here; Candidate Analysis and Talent Leaderboard read it and pass
 * the thresholds to the backend so one policy governs every evaluation in the
 * session. Session-scoped: cleared on logout (mirrors Streamlit).
 */
interface Config {
  strong: number;
  potential: number;
}
interface Ctx extends Config {
  setConfig: (potential: number, strong: number) => void;
  reset: () => void;
}

const KEY = "neuralhire-decision-config";
const DEFAULTS: Config = { strong: DEFAULT_STRONG_FIT, potential: DEFAULT_POTENTIAL_FIT };

const DecisionCtx = createContext<Ctx | null>(null);

export function DecisionConfigProvider({ children }: { children: React.ReactNode }) {
  const [cfg, setCfg] = useState<Config>(DEFAULTS);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(KEY);
      if (raw) setCfg({ ...DEFAULTS, ...JSON.parse(raw) });
    } catch {
      /* ignore */
    }
  }, []);

  const setConfig = useCallback((potential: number, strong: number) => {
    const next = { potential, strong };
    setCfg(next);
    try {
      localStorage.setItem(KEY, JSON.stringify(next));
    } catch {
      /* ignore */
    }
  }, []);

  const reset = useCallback(() => {
    setCfg(DEFAULTS);
    try {
      localStorage.removeItem(KEY);
    } catch {
      /* ignore */
    }
  }, []);

  return <DecisionCtx.Provider value={{ ...cfg, setConfig, reset }}>{children}</DecisionCtx.Provider>;
}

export function useDecisionConfig(): Ctx {
  const ctx = useContext(DecisionCtx);
  if (!ctx) throw new Error("useDecisionConfig must be used within DecisionConfigProvider");
  return ctx;
}
