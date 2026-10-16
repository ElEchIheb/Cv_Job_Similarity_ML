"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, BarChart3, Beaker, FileCheck2, FlaskConical, Gauge, Info, ShieldCheck, TrendingUp, UserRound } from "lucide-react";
import { api } from "@/lib/api/client";
import type { Quality, QualityFigure, QualitySource, VerdictCounts } from "@/lib/api/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/DataStates";
import { cn } from "@/lib/utils";

const METHOD_LABEL: Record<string, string> = {
  hybrid: "Hybrid (shipped)", tfidf: "TF-IDF", skill: "Skills", embedding: "Embeddings",
};
const NOT_MEASURED = "not measured";

/** Number formatter: a missing metric is "not measured", never 0. */
const num = (v: number | null | undefined, d = 3) => (v == null ? NOT_MEASURED : v.toFixed(d));
const ci = (v: [number, number] | null | undefined, d = 3) => (v ? `[${v[0].toFixed(d)}–${v[1].toFixed(d)}]` : "");
const rch = (c: VerdictCounts | null | undefined) => (c ? `${c.REJECT} / ${c.CONSIDER} / ${c.HIRE}` : NOT_MEASURED);

const STATUS: Record<QualitySource["status"], { label: string; tone: "success" | "warning" | "danger" | "accent" | "neutral" }> = {
  current: { label: "Matches shipped calibration", tone: "success" },
  independent_of_calibration: { label: "Raw scores — calibration-independent", tone: "accent" },
  stale: { label: "Computed for another calibration", tone: "warning" },
  unversioned: { label: "Version not recorded", tone: "warning" },
  missing: { label: "Results file missing", tone: "danger" },
  not_measured: { label: "Not measured", tone: "neutral" },
};

export default function QualityPage() {
  const [q, setQ] = useState<Quality | null>(null);
  const [error, setError] = useState(false);
  const [figures, setFigures] = useState<QualityFigure[]>([]);
  const [figUrls, setFigUrls] = useState<Record<string, string>>({});

  useEffect(() => {
    api.quality().then(setQ).catch(() => setError(true));
    api.qualityFigures().then(async (figs) => {
      setFigures(figs);
      const urls: Record<string, string> = {};
      for (const f of figs) { try { urls[f.name] = await api.figureBlob(f.name); } catch { /* skip */ } }
      setFigUrls(urls);
    }).catch(() => {});
  }, []);

  const header = (
    <PageHeader badge="AI Quality Center" title="Evaluation" highlight="evidence & limits"
      subtitle="What has been measured on JobTest, on which data, and what has not. All values are read from versioned result files; nothing is recomputed live." />
  );

  if (error) return <div className="flex flex-col gap-6">{header}<EmptyState icon={<AlertTriangle className="h-8 w-8" />} title="Quality results could not be loaded" desc="The API did not return the evaluation results. Check that the backend is running." /></div>;
  if (!q) return <div className="py-16 text-center text-ink-muted">Loading evaluation results…</div>;
  if (!q.available) return <div className="flex flex-col gap-6">{header}<EmptyState icon={<TrendingUp className="h-8 w-8" />} title="No evaluation results available" desc="Run the evaluation scripts (evaluation/calibration_report.py, evaluation/robustness_probes.py) to produce the versioned result files." /></div>;

  const src = (k: QualitySource["key"]) => q.sources?.find((s) => s.key === k);
  const vq = q.verdict_quality;
  const shipped = q.shipped;
  const stale = (q.sources ?? []).filter((s) => s.status === "stale" || s.status === "unversioned");

  return (
    <div className="flex flex-col gap-6">
      {header}

      {stale.length > 0 && (
        <div className="flex items-start gap-3 rounded-lg bg-warning-soft px-4 py-3 text-caption text-warning-fg ring-1 ring-warning/30">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>Some result files were not produced with the shipped calibration ({stale.map((s) => s.file).join(", ")}). Their figures describe an earlier configuration.</span>
        </div>
      )}

      {/* Shipped configuration */}
      {shipped && (
        <Card elevation={2}>
          <CardHeader><CardTitle className="flex items-center gap-2 text-h4"><ShieldCheck className="h-4 w-4" /> Configuration used by the product</CardTitle></CardHeader>
          <CardBody className="grid gap-4 text-body sm:grid-cols-2 lg:grid-cols-4">
            <Fact label="Model version" value={shipped.model_version} mono />
            <Fact label="Score calibration" value={shipped.calibration_version} mono />
            <Fact label="Fusion weights (TF-IDF / embeddings / skills)" value={shipped.weights ? `${shipped.weights.tfidf} / ${shipped.weights.embedding} / ${shipped.weights.skill}` : NOT_MEASURED} />
            <Fact label="Verdict bands (calibrated score /100)" value={`REJECT < ${shipped.thresholds.potential_fit} ≤ CONSIDER < ${shipped.thresholds.strong_fit} ≤ HIRE`} />
            {shipped.warning && (
              <p className="text-caption text-ink-muted sm:col-span-2 lg:col-span-4">
                Calibration fitted on the {shipped.fitted_on ?? "validation split"}. {shipped.warning}
              </p>
            )}
          </CardBody>
        </Card>
      )}

      {/* Evidence categories */}
      <div className="grid gap-4 md:grid-cols-3">
        <Category icon={<FlaskConical className="h-4 w-4" />} title="Synthetic benchmark" tone="accent"
          text="Generated CV–offer pairs with generator labels. The only source of quantitative metrics (F1, macro-F1, AUC)."
          detail={src("verdicts")?.n ? `Test split: ${src("verdicts")!.n} pairs` : NOT_MEASURED} />
        <Category icon={<Beaker className="h-4 w-4" />} title="Functional trials" tone="success"
          text="Fictitious PDF CVs ranked through the real upload path. Checks extraction, verdicts, history and PDF — no reference labels, so no F1."
          detail={src("fictitious_pdfs")?.n ? `${src("fictitious_pdfs")!.n} fictitious CVs` : NOT_MEASURED} />
        <Category icon={<UserRound className="h-4 w-4" />} title="Student's own CV trials" tone="neutral"
          text="Real CVs belonging to the student, evaluated during development. Qualitative only: without independent reference judgments, no precision or F1 can be computed."
          detail="Metrics: not measured" />
      </div>

      {/* Sources */}
      <Card elevation={1}>
        <CardHeader><CardTitle className="flex items-center gap-2 text-h4"><FileCheck2 className="h-4 w-4" /> Result files</CardTitle></CardHeader>
        <CardBody className="overflow-x-auto">
          <table className="w-full min-w-[680px] text-body">
            <thead><tr className="border-b border-subtle/12 text-caption uppercase tracking-wide text-ink-muted">
              {["Result set", "File", "Generated", "Sample", "Status"].map((h) => <th key={h} className="px-3 py-2 text-left">{h}</th>)}
            </tr></thead>
            <tbody>
              {(q.sources ?? []).map((s) => (
                <tr key={s.key} className="border-b border-subtle/8 last:border-0 align-top">
                  <td className="px-3 py-2.5 text-ink">{s.label}</td>
                  <td className="px-3 py-2.5 font-mono text-caption text-ink-secondary">{s.file ?? "—"}</td>
                  <td className="px-3 py-2.5 tnum text-caption text-ink-secondary">{s.generated ?? "—"}</td>
                  <td className="px-3 py-2.5 tnum text-caption text-ink-secondary">{s.n != null ? `${s.n} ${s.unit ?? ""}` : "—"}</td>
                  <td className="px-3 py-2.5"><Badge status={STATUS[s.status].tone}>{STATUS[s.status].label}</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardBody>
      </Card>

      {/* Verdict quality */}
      <Card elevation={2}>
        <CardHeader><CardTitle className="flex items-center gap-2 text-h4"><Gauge className="h-4 w-4" /> 1. Quality of the displayed verdicts (synthetic test split)</CardTitle></CardHeader>
        <CardBody className="flex flex-col gap-4">
          {!vq ? <Missing what="calibration_report.json" /> : (
            <>
              <Definitions />
              <div className="overflow-x-auto">
                <table className="w-full min-w-[760px] text-body">
                  <thead><tr className="border-b border-subtle/12 text-caption uppercase tracking-wide text-ink-muted">
                    {["Configuration", "Macro-F1, 3 classes [95% CI]", "Binary F1, CONSIDER or better", "F1 of HIRE", "Weighted κ", "Verdicts R / C / H"].map((h) => <th key={h} className="px-3 py-2 text-left">{h}</th>)}
                  </tr></thead>
                  <tbody>
                    {vq.rows.map((r) => (
                      <tr key={r.key} className={cn("border-b border-subtle/8 last:border-0", r.role === "shipped" && "bg-accent/6")}>
                        <td className="px-3 py-2.5 text-ink">{r.label}</td>
                        <td className="px-3 py-2.5 tnum text-ink"><strong>{num(r.macro_f1)}</strong> <span className="text-caption text-ink-muted">{ci(r.macro_f1_95ci)}</span></td>
                        <td className="px-3 py-2.5 tnum text-ink-secondary">{num(r.binary_f1)}</td>
                        <td className="px-3 py-2.5 tnum text-ink-secondary">{num(r.hire_f1)}</td>
                        <td className="px-3 py-2.5 tnum text-ink-secondary">{num(r.kappa)}</td>
                        <td className="px-3 py-2.5 tnum text-ink-secondary">{rch(r.verdict_counts)}</td>
                      </tr>
                    ))}
                    <tr className="text-caption text-ink-muted">
                      <td className="px-3 py-2">Reference: synthetic classes (unrelated / transferable / strong)</td>
                      <td colSpan={4} />
                      <td className="px-3 py-2 tnum">{rch(vq.class_support)}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              {vq.paired_hybrid_minus_tfidf && (
                <p className="text-caption text-ink-secondary">
                  Paired bootstrap on the same {vq.n} pairs: macro-F1 of the shipped hybrid minus TF-IDF = {vq.paired_hybrid_minus_tfidf.mean.toFixed(3)}{" "}
                  (95% CI {ci(vq.paired_hybrid_minus_tfidf.ci95)}). No demonstrated difference between the two.
                </p>
              )}
              <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
                <ConfusionGrid classes={vq.confusion.classes} verdicts={vq.confusion.verdicts} matrix={vq.confusion.matrix} />
                <div className="min-w-0">
                  <div className="mb-2 text-caption font-semibold uppercase tracking-wide text-ink-muted">Per verdict (shipped configuration)</div>
                  <div className="overflow-x-auto">
                  <table className="w-full min-w-[360px] text-body">
                    <thead><tr className="border-b border-subtle/12 text-caption uppercase tracking-wide text-ink-muted">
                      {["Verdict", "Precision", "Recall", "F1", "Pairs in class"].map((h) => <th key={h} className="px-2 py-1.5 text-left">{h}</th>)}
                    </tr></thead>
                    <tbody>
                      {(["REJECT", "CONSIDER", "HIRE"] as const).map((k) => {
                        const p = vq.per_class[k];
                        return (
                          <tr key={k} className="border-b border-subtle/8 last:border-0">
                            <td className="px-2 py-1.5 font-medium text-ink">{k}</td>
                            <td className="px-2 py-1.5 tnum text-ink-secondary">{num(p?.precision)}</td>
                            <td className="px-2 py-1.5 tnum text-ink-secondary">{num(p?.recall)}</td>
                            <td className="px-2 py-1.5 tnum text-ink-secondary">{num(p?.f1)}</td>
                            <td className="px-2 py-1.5 tnum text-ink-secondary">{p?.support ?? NOT_MEASURED}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                  </div>
                  {vq.subgroups.language && Object.keys(vq.subgroups.language).length > 0 && (
                    <p className="mt-3 text-caption text-ink-muted">
                      Macro-F1 by language pair: {Object.entries(vq.subgroups.language).map(([g, v]) => `${g === "cross_lingual" ? "EN CV / FR offer" : g.toUpperCase()} ${v.macro_f1.toFixed(3)} (n = ${v.n})`).join(" · ")}.
                    </p>
                  )}
                </div>
              </div>
            </>
          )}
        </CardBody>
      </Card>

      {/* Raw score ranking */}
      <Card elevation={2}>
        <CardHeader><CardTitle className="flex items-center gap-2 text-h4"><BarChart3 className="h-4 w-4" /> 2. Ranking quality of the raw scores (binary)</CardTitle></CardHeader>
        <CardBody className="flex flex-col gap-3">
          {!q.raw_score ? <Missing what="evaluation_results.json" /> : (
            <>
              <p className="text-caption text-ink-secondary">
                Each raw score (0–1) is read at its own experimental threshold, chosen on the validation split, to separate unrelated pairs from the others.
                This binary F1 measures how well the score <em>ranks</em> pairs; it is not the quality of the three verdicts above and cannot be compared with the macro-F1.
                Test split: {q.raw_score.n ?? NOT_MEASURED} pairs.
              </p>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[720px] text-body">
                  <thead><tr className="border-b border-subtle/12 text-caption uppercase tracking-wide text-ink-muted">
                    {["Method (raw score)", "Experimental threshold", "Precision", "Recall", "Binary F1 [95% CI]", "AUC-ROC", "Time / pair"].map((h) => <th key={h} className="px-3 py-2 text-left">{h}</th>)}
                  </tr></thead>
                  <tbody>
                    {q.raw_score.rows.map((r) => (
                      <tr key={r.key} className={cn("border-b border-subtle/8 last:border-0", r.key === "hybrid" && "bg-accent/6")}>
                        <td className="px-3 py-2.5 text-ink">{METHOD_LABEL[r.key] ?? r.key}</td>
                        <td className="px-3 py-2.5 tnum text-ink-secondary">{num(r.threshold, 4)}</td>
                        <td className="px-3 py-2.5 tnum text-ink-secondary">{num(r.precision)}</td>
                        <td className="px-3 py-2.5 tnum text-ink-secondary">{num(r.recall)}</td>
                        <td className="px-3 py-2.5 tnum text-ink">{num(r.binary_f1)} <span className="text-caption text-ink-muted">{ci(r.binary_f1_95ci)}</span></td>
                        <td className="px-3 py-2.5 tnum text-ink-secondary">{num(r.roc_auc)}</td>
                        <td className="px-3 py-2.5 tnum text-ink-secondary">{r.inference_ms_per_pair == null ? NOT_MEASURED : `${r.inference_ms_per_pair.toFixed(1)} ms`}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </CardBody>
      </Card>

      {/* Robustness */}
      <Card elevation={2}>
        <CardHeader><CardTitle className="flex items-center gap-2 text-h4"><ShieldCheck className="h-4 w-4" /> 3. Robustness to manipulated CVs (synthetic validation split)</CardTitle></CardHeader>
        <CardBody className="flex flex-col gap-3">
          {!q.robustness ? <Missing what="robustness_probes.json" /> : (
            <>
              <p className="text-caption text-ink-secondary">
                Verdicts REJECT / CONSIDER / HIRE for {q.robustness.n_per_probe} modified pairs per scenario, with the same calibration, without and with the evidence check.
                {q.robustness.genuine_pairs && ` On the ${q.robustness.genuine_pairs.n} unmodified validation pairs, the check changed ${q.robustness.genuine_pairs.verdicts_changed} verdicts.`}
              </p>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[640px] text-body">
                  <thead><tr className="border-b border-subtle/12 text-caption uppercase tracking-wide text-ink-muted">
                    {["Scenario", "Without evidence check", "Shipped version"].map((h) => <th key={h} className="px-3 py-2 text-left">{h}</th>)}
                  </tr></thead>
                  <tbody>
                    <tr className="border-b border-subtle/8 text-caption text-ink-muted"><td className="px-3 py-2">Reference: unrelated CVs, unmodified</td><td className="px-3 py-2 tnum" colSpan={2}>{rch(q.robustness.unrelated_reference)}</td></tr>
                    {q.robustness.rows.filter((r) => r.base === "unrelated").map((r) => <ProbeRow key={r.key} label={r.label} before={r.before} after={r.after} />)}
                    <tr className="border-b border-subtle/8 text-caption text-ink-muted"><td className="px-3 py-2">Reference: strong fits, unmodified</td><td className="px-3 py-2 tnum" colSpan={2}>{rch(q.robustness.strong_reference)}</td></tr>
                    {q.robustness.rows.filter((r) => r.base === "strong").map((r) => <ProbeRow key={r.key} label={r.label} before={r.before} after={r.after} />)}
                  </tbody>
                </table>
              </div>
              <p className="text-caption text-ink-muted">Remaining limit: skills written into an experience sentence are still accepted as demonstrated — the text cannot prove the experience is real.</p>
            </>
          )}
        </CardBody>
      </Card>

      {/* Functional & personal trials */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card elevation={1}>
          <CardHeader><CardTitle className="flex items-center gap-2 text-h4"><Beaker className="h-4 w-4" /> 4. Functional trial — fictitious PDF CVs</CardTitle></CardHeader>
          <CardBody className="flex flex-col gap-2 text-body">
            {!q.functional ? <Missing what="functional_trial_fictitious_pdfs.json" /> : (
              <>
                <Fact label="CVs ranked against one full-stack offer" value={String(q.functional.n_cvs ?? NOT_MEASURED)} />
                <Fact label="Verdicts R / C / H" value={rch(q.functional.verdict_counts)} />
                <Fact label="History matches the ranking" value={q.functional.history_consistent == null ? NOT_MEASURED : q.functional.history_consistent ? "yes" : "no"} />
                <Fact label="PDF report generated" value={q.functional.pdf_export_ok ? "yes" : "no"} />
                <p className="text-caption text-ink-muted">Quality tiers of these CVs were set by their author and do not judge fit to this offer: precision and F1 are <strong>not measured</strong>.</p>
              </>
            )}
          </CardBody>
        </Card>
        <Card elevation={1}>
          <CardHeader><CardTitle className="flex items-center gap-2 text-h4"><UserRound className="h-4 w-4" /> 5. Trials with the student&apos;s own CVs</CardTitle></CardHeader>
          <CardBody className="flex flex-col gap-2 text-body">
            <Fact label="Precision / recall / F1" value="not measured" />
            <p className="text-caption text-ink-secondary">
              The student evaluated their own CVs against real job offers to check the complete flow on authentic documents. These runs have no independent
              reference judgment, so they are reported as qualitative observations only; no personal data is shown here.
            </p>
          </CardBody>
        </Card>
      </div>

      {/* Charts */}
      {figures.length > 0 && (
        <Card elevation={2}>
          <CardHeader><CardTitle className="text-h4">Charts (synthetic test split{figures[0]?.n ? `, n = ${figures[0].n}` : ""})</CardTitle></CardHeader>
          <CardBody className="flex flex-col gap-5">
            {figures.some((f) => f.stale) && (
              <div className="flex items-center gap-2 text-caption text-warning-fg"><AlertTriangle className="h-4 w-4" /> These charts were generated for another calibration version.</div>
            )}
            {(["verdicts", "ranking"] as const).map((g) => {
              const fs = figures.filter((f) => (f.group ?? "verdicts") === g);
              if (!fs.length) return null;
              return (
                <div key={g}>
                  <div className="mb-2 text-caption font-semibold uppercase tracking-wide text-ink-muted">
                    {g === "verdicts" ? "Displayed verdicts (calibrated score, 3 classes)" : "Raw scores (ranking)"}
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    {fs.map((f) => (
                      <figure key={f.name}>
                        {figUrls[f.name]
                          ? <img src={figUrls[f.name]} alt={f.label} className="w-full rounded-lg border border-subtle/12 bg-white" />
                          : <div className="h-40 animate-pulse rounded-lg bg-surface-overlay" />}
                        <figcaption className="mt-1.5 text-caption text-ink-muted">{f.label}</figcaption>
                      </figure>
                    ))}
                  </div>
                </div>
              );
            })}
          </CardBody>
        </Card>
      )}
    </div>
  );
}

function Fact({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="min-w-0">
      <div className="text-caption text-ink-muted">{label}</div>
      <div className={cn("break-words font-medium text-ink", mono && "font-mono text-caption", value === NOT_MEASURED && "font-normal italic text-ink-muted")}>{value}</div>
    </div>
  );
}

function Category({ icon, title, text, detail, tone }: { icon: React.ReactNode; title: string; text: string; detail: string; tone: "accent" | "success" | "neutral" }) {
  const t = { accent: "text-accent-300 bg-accent/12", success: "text-success-fg bg-success-soft", neutral: "text-ink-secondary bg-surface-raised" }[tone];
  return (
    <div className="flex flex-col gap-2 rounded-xl border border-subtle/12 bg-surface p-5 shadow-e2">
      <div className="flex items-center gap-2">
        <span className={cn("inline-grid h-8 w-8 place-items-center rounded-lg", t)}>{icon}</span>
        <span className="font-medium text-ink">{title}</span>
      </div>
      <p className="text-caption text-ink-secondary">{text}</p>
      <p className="mt-auto text-caption font-medium text-ink">{detail}</p>
    </div>
  );
}

function Definitions() {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-subtle/12 bg-accent/6 px-4 py-3 text-caption text-ink-secondary">
      <Info className="mt-0.5 h-4 w-4 shrink-0 text-accent-300" />
      <div className="flex flex-col gap-1">
        <span><strong className="text-ink">Macro-F1 (3 classes)</strong>: mean of the F1 of REJECT, CONSIDER and HIRE against the generator classes unrelated / transferable / strong. This is the quality of the verdicts a recruiter sees.</span>
        <span><strong className="text-ink">Binary F1</strong>: CONSIDER-or-better versus unrelated pairs only. It ignores the CONSIDER / HIRE boundary and is not comparable with the macro-F1.</span>
        <span>Labels are synthetic: these values do not validate real hiring decisions.</span>
      </div>
    </div>
  );
}

function ConfusionGrid({ classes, verdicts, matrix }: { classes: string[]; verdicts: string[]; matrix: number[][] }) {
  return (
    <div className="min-w-0">
      <div className="mb-2 text-caption font-semibold uppercase tracking-wide text-ink-muted">Confusion matrix — synthetic class (rows) × verdict shown (columns)</div>
      <div className="grid grid-cols-[minmax(64px,auto)_repeat(3,minmax(0,1fr))] gap-1 text-caption">
        <div />
        {verdicts.map((v) => <div key={v} className="px-1 py-1 text-center font-semibold text-ink-secondary">{v}</div>)}
        {matrix.map((row, i) => {
          const total = row.reduce((a, b) => a + b, 0) || 1;
          return [
            <div key={`l${i}`} className="flex flex-col justify-center pr-1 text-ink-secondary">{classes[i]}<span className="text-micro text-ink-muted">n = {total}</span></div>,
            ...row.map((v, j) => {
              const share = v / total;
              return (
                <div key={`${i}-${j}`} className={cn("rounded-md px-1 py-2 text-center tnum", i === j ? "ring-1 ring-accent/40" : "")}
                  style={{ background: `rgb(124 92 255 / ${0.08 + share * 0.6})` }}>
                  <div className="font-semibold text-ink">{v}</div>
                  <div className="text-micro text-ink-secondary">{(share * 100).toFixed(0)}%</div>
                </div>
              );
            }),
          ];
        })}
      </div>
    </div>
  );
}

function ProbeRow({ label, before, after }: { label: string; before: VerdictCounts; after: VerdictCounts }) {
  return (
    <tr className="border-b border-subtle/8 last:border-0">
      <td className="px-3 py-2.5 text-ink">{label}</td>
      <td className="px-3 py-2.5 tnum text-ink-secondary">{rch(before)}</td>
      <td className={cn("px-3 py-2.5 tnum", after.HIRE < before.HIRE ? "text-success-fg" : "text-ink")}>{rch(after)}</td>
    </tr>
  );
}

function Missing({ what }: { what: string }) {
  return (
    <div className="flex items-center gap-2 rounded-lg bg-surface-raised/50 px-4 py-3 text-caption text-ink-muted">
      <AlertTriangle className="h-4 w-4" /> Not measured — the results file <code className="font-mono">{what}</code> is missing or unreadable.
    </div>
  );
}
