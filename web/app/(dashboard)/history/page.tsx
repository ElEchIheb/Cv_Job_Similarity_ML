"use client";

import { useEffect, useMemo, useState } from "react";
import { FileText, Filter, RefreshCw } from "lucide-react";
import { api } from "@/lib/api/client";
import type { MatchDetail, MatchRow } from "@/lib/api/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Table, type Column } from "@/components/ui/Table";
import { EmptyState, SkeletonTable, ProgressMini } from "@/components/ui/DataStates";
import { Input, Select, Label } from "@/components/ui/Field";
import { useToast } from "@/components/ui/Toast";
import { BAND_LABEL, DECISION_STATUS } from "@/lib/constants";

export default function HistoryPage() {
  const toast = useToast();
  const [rows, setRows] = useState<MatchRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [fCode, setFCode] = useState("");
  const [fTitle, setFTitle] = useState("");
  const [fEmail, setFEmail] = useState("");
  const [selected, setSelected] = useState<number | null>(null);
  const [detail, setDetail] = useState<MatchDetail | null>(null);

  const load = () => {
    setLoading(true);
    api.matches().then(setRows).catch((e) => toast("error", e.message)).finally(() => setLoading(false));
  };
  useEffect(load, []); // eslint-disable-line react-hooks/exhaustive-deps

  const filtered = useMemo(() => rows.filter((m) =>
    (!fCode || (m.job_code ?? "").toLowerCase().includes(fCode.toLowerCase())) &&
    (!fTitle || m.job_title.toLowerCase().includes(fTitle.toLowerCase())) &&
    (!fEmail || (m.candidate_email ?? "").toLowerCase().includes(fEmail.toLowerCase())),
  ), [rows, fCode, fTitle, fEmail]);

  useEffect(() => {
    if (filtered.length && !filtered.some((m) => m.id === selected)) setSelected(filtered[0].id);
  }, [filtered, selected]);

  useEffect(() => {
    if (selected == null) { setDetail(null); return; }
    api.matchDetail(selected).then(setDetail).catch(() => setDetail(null));
  }, [selected]);

  const columns: Column<MatchRow>[] = [
    { key: "candidate_name", header: "Candidate", sortable: true, sortValue: (m) => m.candidate_name.toLowerCase(), render: (m) => <span className="font-medium text-ink">{m.candidate_name}</span> },
    { key: "candidate_email", header: "Email", render: (m) => <span className="text-caption text-ink-muted">{m.candidate_email ?? "N/A"}</span> },
    { key: "job_title", header: "Job Offer", sortable: true, sortValue: (m) => m.job_title.toLowerCase(), render: (m) => m.job_title },
    { key: "job_code", header: "Code", render: (m) => <span className="font-mono text-caption text-ink-muted">{m.job_code ?? "N/A"}</span> },
    { key: "final_score", header: "Compatibility", sortable: true, sortValue: (m) => m.final_score ?? -1, render: (m) => <ProgressMini value={m.final_score ?? 0} /> },
    { key: "decision", header: "Decision", align: "center", render: (m) => m.decision ? <Badge status={DECISION_STATUS[m.decision]}>{BAND_LABEL[m.decision]}</Badge> : <Badge status="neutral">N/A</Badge> },
    { key: "created_at", header: "Date", sortable: true, sortValue: (m) => m.created_at ?? "", render: (m) => <span className="text-caption text-ink-muted">{m.created_at ? new Date(m.created_at).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" }) : "N/A"}</span> },
  ];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between gap-4">
        <PageHeader badge="Evaluations" title="Analysis" highlight="History" subtitle="Review previous AI matching evaluations and inspect their raw explanation payloads." />
        <Button variant="ghost" size="sm" icon={<RefreshCw className="h-3.5 w-3.5" />} onClick={load} className="mt-2" />
      </div>

      <Card elevation={1}>
        <CardHeader><CardTitle className="flex items-center gap-2 text-h4"><Filter className="h-4 w-4" /> Filter Analyses</CardTitle></CardHeader>
        <CardBody className="grid gap-4 sm:grid-cols-3">
          <label className="block"><Label>Job Offer Code</Label><Input value={fCode} onChange={(e) => setFCode(e.target.value)} placeholder="e.g. JOB-2026-001" /></label>
          <label className="block"><Label>Job Offer Title</Label><Input value={fTitle} onChange={(e) => setFTitle(e.target.value)} placeholder="e.g. Engineer" /></label>
          <label className="block"><Label>Candidate Email</Label><Input value={fEmail} onChange={(e) => setFEmail(e.target.value)} placeholder="e.g. alice@" /></label>
        </CardBody>
      </Card>

      {loading ? <SkeletonTable /> : filtered.length === 0 ? (
        <EmptyState icon={<FileText className="h-8 w-8" />} title="No analyses found" desc="Adjust your filters or run a new evaluation." />
      ) : (
        <>
          <Table columns={columns} rows={filtered} keyOf={(m) => m.id} />
          <Card elevation={2}>
            <CardHeader>
              <CardTitle className="text-h4">Report details</CardTitle>
              <Select value={selected ?? ""} onChange={(e) => setSelected(Number(e.target.value))} className="max-w-[220px]">
                {filtered.map((m) => <option key={m.id} value={m.id}>#{m.id} — {m.candidate_name}</option>)}
              </Select>
            </CardHeader>
            <CardBody>
              <p className="mb-3 text-caption text-ink-muted">Raw JSON explanation payload from the AI for the selected evaluation.</p>
              <pre className="max-h-[420px] overflow-auto rounded-lg bg-surface-raised/60 p-4 font-mono text-caption text-ink-secondary">
                {detail ? JSON.stringify(detail.raw, null, 2) : "Loading…"}
              </pre>
            </CardBody>
          </Card>
        </>
      )}
    </div>
  );
}
