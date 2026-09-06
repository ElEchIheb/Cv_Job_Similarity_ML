"use client";

import { useEffect, useState } from "react";
import { ArrowLeftRight, Briefcase, Edit, Plus, RefreshCw, Target, Trash2, Users, XCircle } from "lucide-react";
import { api, type JobInput } from "@/lib/api/client";
import type { JobOffer, JobStatus } from "@/lib/api/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { StatCard } from "@/components/ui/StatCard";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Table, type Column } from "@/components/ui/Table";
import { EmptyState, SkeletonTable } from "@/components/ui/DataStates";
import { Modal } from "@/components/ui/Modal";
import { Input, Select, Textarea, Label } from "@/components/ui/Field";
import { useToast } from "@/components/ui/Toast";
import { staggerContainer } from "@/lib/motion";
import { JOB_STATUSES } from "@/lib/constants";
import { motion } from "framer-motion";

const STATUS_TONE: Record<JobStatus, "success" | "warning" | "neutral"> = {
  OPEN: "success", ON_HOLD: "warning", CLOSED: "neutral",
};

export default function JobsPage() {
  const toast = useToast();
  const [offers, setOffers] = useState<JobOffer[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<JobOffer | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [toDelete, setToDelete] = useState<JobOffer | null>(null);

  const load = () => {
    setLoading(true);
    api.jobOffers().then(setOffers).catch((e) => toast("error", e.message)).finally(() => setLoading(false));
  };
  useEffect(load, []); // eslint-disable-line react-hooks/exhaustive-deps

  const openNew = () => { setEditing(null); setShowForm(true); };
  const openEdit = (o: JobOffer) => { setEditing(o); setShowForm(true); };

  const toggle = async (o: JobOffer) => {
    try { await api.toggleJobStatus(o.id); toast("success", "Job status updated."); load(); }
    catch (e) { toast("error", e instanceof Error ? e.message : "Failed."); }
  };

  const confirmDelete = async () => {
    if (!toDelete) return;
    try { await api.deleteJob(toDelete.id); toast("success", "Job offer deleted."); setToDelete(null); load(); }
    catch (e) { toast("error", e instanceof Error ? e.message : "Failed."); }
  };

  const openRoles = offers.filter((o) => o.status === "OPEN").length;
  const closedRoles = offers.filter((o) => o.status === "CLOSED").length;
  const totalEvals = offers.reduce((s, o) => s + o.evaluation_count, 0);

  const columns: Column<JobOffer>[] = [
    { key: "job_code", header: "Code", sortable: true, sortValue: (o) => o.job_code ?? "", render: (o) => <span className="font-mono text-caption text-ink-secondary">{o.job_code ?? "N/A"}</span> },
    { key: "title", header: "Title", sortable: true, sortValue: (o) => o.title.toLowerCase(), render: (o) => <span className="font-medium text-ink">{o.title}</span> },
    { key: "evaluation_count", header: "Evaluations", align: "center", sortable: true, sortValue: (o) => o.evaluation_count, render: (o) => <span className="tnum">{o.evaluation_count}</span> },
    { key: "created_at", header: "Created", sortable: true, sortValue: (o) => o.created_at ?? "", render: (o) => <span className="text-caption text-ink-muted">{o.created_at ? new Date(o.created_at).toLocaleDateString() : "N/A"}</span> },
    { key: "status", header: "Status", align: "center", render: (o) => <Badge status={STATUS_TONE[o.status]}>{o.status.replace("_", " ")}</Badge> },
    {
      key: "actions", header: "", align: "right", render: (o) => (
        <div className="flex justify-end gap-1">
          <IconBtn title="Edit" onClick={() => openEdit(o)}><Edit className="h-4 w-4" /></IconBtn>
          <IconBtn title="Toggle status" onClick={() => toggle(o)}><ArrowLeftRight className="h-4 w-4" /></IconBtn>
          <IconBtn title="Delete" danger onClick={() => setToDelete(o)}><Trash2 className="h-4 w-4" /></IconBtn>
        </div>
      ),
    },
  ];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between gap-4">
        <PageHeader badge="Positions" title="Job" highlight="Offers" subtitle="Manage open positions and view their requirements." />
        <div className="flex shrink-0 gap-2 pt-2">
          <Button variant="ghost" size="sm" icon={<RefreshCw className="h-3.5 w-3.5" />} onClick={load} />
          <Button icon={<Plus className="h-4 w-4" />} onClick={openNew}>Add New Job</Button>
        </div>
      </div>

      <motion.div variants={staggerContainer(0.05)} initial="hidden" animate="show" className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Total Positions" value={offers.length} icon={<Briefcase className="h-5 w-5" />} tone="accent" />
        <StatCard label="Open Roles" value={openRoles} icon={<Target className="h-5 w-5" />} tone="cyan" />
        <StatCard label="Candidates Evaluated" value={totalEvals} icon={<Users className="h-5 w-5" />} tone="success" />
        <StatCard label="Closed Roles" value={closedRoles} icon={<XCircle className="h-5 w-5" />} tone="warning" />
      </motion.div>

      {loading ? <SkeletonTable /> : (
        <Table columns={columns} rows={offers} keyOf={(o) => o.id}
          empty={<EmptyState icon={<Briefcase className="h-8 w-8" />} title="No job offers" desc="Add a new job offer to begin evaluating candidates." action={<Button icon={<Plus className="h-4 w-4" />} onClick={openNew}>Add New Job</Button>} />} />
      )}

      <JobFormModal open={showForm} onClose={() => setShowForm(false)} editing={editing} onSaved={() => { setShowForm(false); load(); }} toast={toast} />

      <Modal open={!!toDelete} onClose={() => setToDelete(null)} title="Delete Job Offer">
        <div className="flex flex-col gap-4">
          <div className="font-medium text-ink">{toDelete?.job_code}: {toDelete?.title}</div>
          {toDelete && toDelete.evaluation_count > 0 ? (
            <div className="rounded-lg bg-warning-soft px-4 py-3 text-body text-warning-fg">
              This job offer cannot be permanently deleted because it has {toDelete.evaluation_count} associated evaluation(s). Set its status to CLOSED instead.
            </div>
          ) : (
            <p className="text-body text-ink-secondary">This job offer has 0 applications. Are you sure you want to delete it?</p>
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

function JobFormModal({ open, onClose, editing, onSaved, toast }: {
  open: boolean; onClose: () => void; editing: JobOffer | null; onSaved: () => void;
  toast: (k: "success" | "error" | "info", m: string) => void;
}) {
  const [form, setForm] = useState<JobInput>({ title: "", description: "", required_skills: "", status: "OPEN" });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open) setForm(editing
      ? { title: editing.title, description: editing.description, required_skills: editing.required_skills_raw, status: editing.status }
      : { title: "", description: "", required_skills: "", status: "OPEN" });
  }, [open, editing]);

  const save = async () => {
    if (!form.title.trim() || !form.description.trim()) return toast("error", "Title and Description are required.");
    setSaving(true);
    try {
      if (editing) { await api.updateJob(editing.id, form); toast("success", "Job Offer updated."); }
      else { const j = await api.createJob(form); toast("success", `Job Offer created: ${j.job_code}`); }
      onSaved();
    } catch (e) { toast("error", e instanceof Error ? e.message : "Failed."); }
    finally { setSaving(false); }
  };

  return (
    <Modal open={open} onClose={onClose} title={editing ? "Edit Job Offer" : "Add Job Offer"} className="max-w-2xl">
      <div className="flex flex-col gap-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-[2fr_1fr]">
          <label className="block"><Label>Job Title *</Label>
            <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="e.g. Senior ML Engineer" /></label>
          <label className="block"><Label>Status</Label>
            <Select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value as JobStatus })}>
              {JOB_STATUSES.map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
            </Select></label>
        </div>
        <label className="block"><Label>Job Description *</Label>
          <Textarea rows={6} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Describe the role, responsibilities and requirements…" /></label>
        <label className="block"><Label>Required Skills (comma separated)</Label>
          <Input value={form.required_skills} onChange={(e) => setForm({ ...form, required_skills: e.target.value })} placeholder="Python, PyTorch, Docker, AWS" /></label>
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button loading={saving} onClick={save}>{editing ? "Update Job Offer" : "Create Job Offer"}</Button>
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

