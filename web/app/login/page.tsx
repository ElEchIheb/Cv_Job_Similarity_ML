"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowRight, Lock, Mail, User as UserIcon } from "lucide-react";
import { api } from "@/lib/api/client";
import { useToast } from "@/components/ui/Toast";
import { Button } from "@/components/ui/Button";
import { Logo } from "@/components/layout/Logo";
import { AmbientBackground } from "@/components/three/AmbientBackground";
import { staggerContainer, fadeUp } from "@/lib/motion";

export default function LoginPage() {
  const router = useRouter();
  const toast = useToast();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("wajihhassyoui123@gmail.com");
  const [password, setPassword] = useState("demo1234");
  const [confirm, setConfirm] = useState("demo1234");
  const [name, setName] = useState("Wajih Hassyoui");
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (mode === "register") {
      if (!name || !email || !password) {
        toast("error", "Please fill in all fields.");
        return;
      }
      if (password !== confirm) {
        toast("error", "Passwords do not match.");
        return;
      }
    } else if (!email || !password) {
      toast("error", "Please fill in all fields.");
      return;
    }
    setLoading(true);
    try {
      if (mode === "register") {
        await api.register(email, password, name);
        toast("success", "Account created successfully. Please sign in.");
        setMode("login");
        setLoading(false);
        return;
      }
      await api.login(email, password);
      router.push("/overview");
    } catch (err) {
      toast("error", err instanceof Error ? err.message : "Something went wrong.");
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen bg-canvas lg:grid lg:grid-cols-[1.1fr_1fr]">
      {/* ── Ambient hero panel ─────────────────────────────────── */}
      <div className="relative hidden overflow-hidden border-r border-subtle/10 lg:block">
        <AmbientBackground intensity={1.2} parallax />
        <div className="bg-grid absolute inset-0 opacity-60" />
        <div className="relative z-10 flex h-full flex-col justify-between p-10">
          <Logo />
          <motion.div variants={staggerContainer(0.08)} initial="hidden" animate="show" className="max-w-md">
            <motion.div variants={fadeUp} className="mb-4 inline-flex items-center gap-2 rounded-full border border-subtle/15 glass px-3 py-1 text-caption text-ink-secondary">
              <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse-glow" />
              Precision Intelligence for hiring
            </motion.div>
            <motion.h1 variants={fadeUp} className="font-display text-display font-bold leading-[1.02] text-ink">
              Evaluate talent with a <span className="text-gradient">diagnostic&nbsp;instrument</span>, not a spreadsheet.
            </motion.h1>
            <motion.p variants={fadeUp} className="mt-5 text-body-lg text-ink-secondary">
              NeuralHire fuses semantic, keyword, and skill signals into one confident, explainable verdict — with the evidence to back it.
            </motion.p>
          </motion.div>
          <motion.div variants={fadeUp} initial="hidden" animate="show" className="flex gap-8 text-caption text-ink-muted">
            <div>
              <div className="font-display text-h3 font-semibold text-ink tnum">4</div>
              <div>fused models</div>
            </div>
            <div>
              <div className="font-display text-h3 font-semibold text-ink tnum">&lt;0.5s</div>
              <div>per evaluation</div>
            </div>
            <div>
              <div className="font-display text-h3 font-semibold text-ink tnum">100%</div>
              <div>explainable</div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* ── Auth card ──────────────────────────────────────────── */}
      <div className="relative flex min-h-screen items-center justify-center p-6">
        <div className="absolute inset-0 lg:hidden">
          <AmbientBackground intensity={0.8} />
        </div>
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: "spring", stiffness: 220, damping: 26 }}
          className="relative z-10 w-full max-w-sm rounded-xl border border-subtle/12 bg-surface/90 p-7 shadow-e4 backdrop-blur-glass"
        >
          <div className="mb-6 lg:hidden">
            <Logo />
          </div>
          <h2 className="font-display text-h2 font-semibold text-ink">
            {mode === "login" ? "Welcome back" : "Create account"}
          </h2>
          <p className="mt-1 text-body text-ink-secondary">
            {mode === "login" ? "Sign in to your evaluation workspace." : "Start evaluating candidates in minutes."}
          </p>

          <form onSubmit={submit} className="mt-6 flex flex-col gap-3.5">
            {mode === "register" && (
              <Field icon={<UserIcon className="h-4 w-4" />} label="Full name" value={name} onChange={setName} placeholder="Jane Recruiter" />
            )}
            <Field icon={<Mail className="h-4 w-4" />} label="Email" type="email" value={email} onChange={setEmail} placeholder="you@company.com" />
            <Field icon={<Lock className="h-4 w-4" />} label="Password" type="password" value={password} onChange={setPassword} placeholder="••••••••" />
            {mode === "register" && (
              <Field icon={<Lock className="h-4 w-4" />} label="Confirm password" type="password" value={confirm} onChange={setConfirm} placeholder="••••••••" />
            )}

            <Button type="submit" size="lg" loading={loading} className="mt-2 w-full" icon={<ArrowRight className="h-4 w-4" />}>
              {mode === "login" ? "Sign in" : "Create account"}
            </Button>
          </form>

          <button
            onClick={() => setMode(mode === "login" ? "register" : "login")}
            className="mt-5 w-full text-center text-caption text-ink-secondary transition-colors hover:text-ink"
          >
            {mode === "login" ? "No account yet? " : "Already registered? "}
            <span className="font-medium text-accent-300">{mode === "login" ? "Create one" : "Sign in"}</span>
          </button>
        </motion.div>
      </div>
    </div>
  );
}

function Field({
  icon,
  label,
  value,
  onChange,
  type = "text",
  placeholder,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-caption font-medium text-ink-secondary">{label}</span>
      <span className="flex items-center gap-2.5 rounded-lg border border-subtle/15 bg-surface-raised px-3 transition-colors focus-within:border-accent/50 focus-within:ring-2 focus-within:ring-accent/20">
        <span className="text-ink-muted">{icon}</span>
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="h-11 w-full bg-transparent text-body text-ink outline-none placeholder:text-ink-muted"
        />
      </span>
    </label>
  );
}
