"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Activity, Clock, Edit, RefreshCw, Trash2, TrendingUp, Users } from "lucide-react";
import { api, type CandidateInput } from "@/lib/api/client";
import type { Candidate, CandidateStatus } from "@/lib/api/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatCard } from "@/components/ui/StatCard";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Table, type Column } from "@/components/ui/Table";
import { EmptyState, SkeletonTable, ProgressMini } from "@/components/ui/DataStates";
import { Modal } from "@/components/ui/Modal";
import { Input, Select, Label } from "@/components/ui/Field";
import { useToast } from "@/components/ui/Toast";
import { staggerContainer } from "@/lib/motion";
import { CANDIDATE_STATUSES } from "@/lib/constants";

const STATUS_TONE: Record<CandidateStatus, "success" | "warning" | "danger" | "accent" | "neutral"> = {
  HIRED: "success", SHORTLISTED: "warning", INTERVIEW: "warning",
  UNDER_REVIEW: "accent", REJECTED: "danger", NEW: "neutral",
};

export default function CandidatesPage() {
  const toast = useToast();
  const [cands, setCands] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<Candidate | null>(null);
  const [toDelete, setToDelete] = useState<Candidate | null>(null);

  const load = () => {
    setLoading(true);
    api.candidates().then(setCands).catch((e) => toast("error", e.message)).finally(() => setLoading(false));
  };
  useEffect(load, []); // eslint-disable-line react-hooks/exhaustive-deps

  const confirmDelete = async () => {
    if (!toDelete) return;
    try { await api.deleteCandidate(toDelete.id); toast("success", "Candidate deleted."); setToDelete(null); load(); }
    catch (e) { toast("error", e instanceof Error ? e.message : "Failed."); }
  };

  const totalEvals = cands.reduce((s, c) => s + c.evaluation_count, 0);
  const scored = cands.filter((c) => c.best_score != null);
  const avg = scored.length ? (scored.reduce((s, c) => s + (c.best_score ?? 0), 0) / scored.length) * 100 : 0;

  const columns: Column<Candidate>[] = [
    { key: "full_name", header: "Candidate", sortable: true, sortValue: (c) => c.full_name.toLowerCase(), render: (c) => <span className="font-medium text-ink">{c.full_name}</span> },
    { key: "email", header: "Email", render: (c) => <span className="text-caption text-ink-muted">{c.email ?? "N/A"}</span> },
    { key: "evaluation_count", header: "Evaluations", align: "center", sortable: true, sortValue: (c) => c.evaluation_count, render: (c) => <span className="tnum">{c.evaluation_count}</span> },
    { key: "best_score", header: "Best Match", sortable: true, sortValue: (c) => c.best_score ?? -1, render: (c) => c.best_score != null ? <ProgressMini value={c.best_score} /> : <span className="text-caption text-ink-muted">Not evaluated</span> },
    { key: "created_at", header: "Created", sortable: true, sortValue: (c) => c.created_at ?? "", render: (c) => <span className="text-caption text-ink-muted">{c.created_at ? new Date(c.created_at).toLocaleDateString() : "N/A"}</span> },
    { key: "status", header: "Status", align: "center", render: (c) => <Badge status={STATUS_TONE[c.status]}>{c.status.replace("_", " ")}</Badge> },
    {
      key: "actions", header: "", align: "right", render: (c) => (
        <div className="flex justify-end gap-1">
          <IconBtn title="Edit" onClick={() => setEditing(c)}><Edit className="h-4 w-4" /></IconBtn>
          <IconBtn title="Delete" danger onClick={() => setToDelete(c)}><Trash2 className="h-4 w-4" /></IconBtn>
        </div>
      ),
    },
  ];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between gap-4">
        <PageHeader badge="Candidates" title="Candidate" highlight="History" subtitle="Review candidates, parsed profiles and their evaluation activity." />
        <Button variant="ghost" size="sm" icon={<RefreshCw className="h-3.5 w-3.5" />} onClick={load} className="mt-2" />
      </div>

      <motion.div variants={staggerContainer(0.05)} initial="hidden" animate="show" className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Total Candidates" value={cands.length} icon={<Users className="h-5 w-5" />} tone="accent" />
        <StatCard label="Total Evaluations" value={totalEvals} icon={<Activity className="h-5 w-5" />} tone="cyan" />
        <StatCard label="Avg Compatibility" value={avg} suffix="%" decimals={1} icon={<TrendingUp className="h-5 w-5" />} tone="success" />
        <StatCard label="Best-scored" value={scored.length} icon={<Clock className="h-5 w-5" />} tone="warning" />
      </motion.div>

      {loading ? <SkeletonTable /> : (
        <Table columns={columns} rows={cands} keyOf={(c) => c.id}
          empty={<EmptyState icon={<Users className="h-8 w-8" />} title="No candidates yet" desc="Run a candidate evaluation to begin building your history." />} />
      )}

      <EditModal open={!!editing} candidate={editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); load(); }} toast={toast} />

      <Modal open={!!toDelete} onClose={() => setToDelete(null)} title="Delete Candidate">
        <div className="flex flex-col gap-4">
          <div>
            <div className="font-medium text-ink">{toDelete?.full_name}</div>
            <div className="text-caption text-ink-muted">{toDelete?.email ?? "No email"}</div>
          </div>
          {toDelete && toDelete.evaluation_count > 0 ? (
            <div className="rounded-lg bg-warning-soft px-4 py-3 text-body text-warning-fg">
              Cannot permanently delete this candidate because they have {toDelete.evaluation_count} existing application(s). Change their pipeline status instead.
            </div>
          ) : (
            <p className="text-body text-ink-secondary">This candidate has 0 applications. Are you sure you want to delete them?</p>
          )}
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setToDelete(null)}>Cancel</Button>
            {toDelete && toDelete.evaluation_count === 0 && <Button variant="danger" onClick={confirmDelete}>Delete</Button>}
          </div>
        </div>
      </Modal>
    </div>
  );
}

function EditModal({ open, candidate, onClose, onSaved, toast }: {
  open: boolean; candidate: Candidate | null; onClose: () => void; onSaved: () => void;
  toast: (k: "success" | "error" | "info", m: string) => void;
}) {
  const [form, setForm] = useState<CandidateInput>({ full_name: "", email: "", phone: "", status: "NEW" });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open && candidate) setForm({
      full_name: candidate.full_name, email: candidate.email ?? "", phone: candidate.phone ?? "", status: candidate.status,
    });
  }, [open, candidate]);

  const save = async () => {
    if (!form.full_name.trim()) return toast("error", "Candidate Name is required.");
    if (!candidate) return;
    setSaving(true);
    try {
      await api.updateCandidate(candidate.id, { ...form, email: form.email?.trim() || null, phone: form.phone?.trim() || null });
      toast("success", "Candidate updated."); onSaved();
    } catch (e) { toast("error", e instanceof Error ? e.message : "Failed."); }
    finally { setSaving(false); }
  };

  return (
    <Modal open={open} onClose={onClose} title="Edit Candidate">
      <div className="flex flex-col gap-4">
        <label className="block"><Label>Candidate Name *</Label>
          <Input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} /></label>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <label className="block"><Label>Email</Label>
            <Input value={form.email ?? ""} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="name@example.com" /></label>
          <label className="block"><Label>Phone</Label>
            <Input value={form.phone ?? ""} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></label>
        </div>
        <label className="block"><Label>Pipeline Status</Label>
          <Select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value as CandidateStatus })}>
            {CANDIDATE_STATUSES.map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
          </Select></label>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button loading={saving} onClick={save}>Save Changes</Button>
        </div>
      </div>
    </Modal>
  );
}

function IconBtn({ children, title, onClick, danger }: { children: React.ReactNode; title: string; onClick: () => void; danger?: boolean }) {
  return (
    <button title={title} onClick={onClick}
      className={`grid h-8 w-8 place-items-center rounded-md text-ink-muted transition-colors hover:bg-surface-overlay ${danger ? "hover:text-danger-fg" : "hover:text-ink"}`}>
      {children}
    </button>
  );
}
