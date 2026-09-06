"use client";

import { motion } from "framer-motion";
import { AlertTriangle, Check, Plus, X } from "lucide-react";
import { Pill } from "@/components/ui/Pill";
import { staggerContainer, fadeUp } from "@/lib/motion";

type Group = "matched" | "missing" | "extra" | "priority";

const META: Record<Group, { title: string; tone: Group; icon: React.ReactNode }> = {
  matched: { title: "Detected skills", tone: "matched", icon: <Check className="h-3 w-3" /> },
  priority: { title: "Priority gaps", tone: "priority", icon: <AlertTriangle className="h-3 w-3" /> },
  missing: { title: "Missing skills", tone: "missing", icon: <X className="h-3 w-3" /> },
  extra: { title: "Additional skills", tone: "extra", icon: <Plus className="h-3 w-3" /> },
};

export function SkillChipGroup({ group, skills }: { group: Group; skills: string[] }) {
  if (!skills.length) return null;
  const meta = META[group];
  return (
    <div>
      <div className="mb-2 flex items-center gap-2 text-caption font-medium text-ink-secondary">
        {meta.title}
        <span className="tnum rounded-full bg-surface-overlay px-1.5 text-ink-muted">{skills.length}</span>
      </div>
      <motion.div
        variants={staggerContainer(0.025)}
        initial="hidden"
        animate="show"
        className="flex flex-wrap gap-2"
      >
        {skills.map((s) => (
          <motion.div key={s} variants={fadeUp}>
            <Pill tone={meta.tone} icon={meta.icon}>
              {s}
            </Pill>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
