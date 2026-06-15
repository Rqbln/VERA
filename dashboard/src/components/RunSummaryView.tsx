"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { listRuns, getRunSummary } from "@/lib/api";
import { getToken, isGuided } from "@/lib/auth";
import { RunSelector } from "./RunSelector";
import { LifecycleRail } from "./LifecycleRail";
import { CoverageBar } from "./CoverageBar";
import { ComplaiTriageTable } from "./ComplaiTriageTable";
import { NonMeasurableStrip } from "./NonMeasurableStrip";
import { HarnessProvenanceTable } from "./HarnessProvenanceTable";
import { TrustFactorCard } from "./TrustFactorCard";
import { TrendCurve } from "./TrendCurve";
import { HitlReviewPanel } from "./HitlReviewPanel";
import { DeclarativeForms } from "./DeclarativeForms";
import { downloadAuditPdf } from "@/lib/api";
import { useEffect, useState } from "react";

interface Props {
  lens: "compliance" | "cyber" | "ds";
  defaultRunId?: string;
}

export function RunSummaryView({ lens, defaultRunId }: Props) {
  const token = getToken();
  const [lifecycleFilter, setLifecycleFilter] = useState("");
  const [stageRail, setStageRail] = useState("inference");
  const [runId, setRunId] = useState<string | null>(defaultRunId || null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [trendReq, setTrendReq] = useState("R02");
  const [pdfError, setPdfError] = useState<string | null>(null);

  const { data: runList } = useQuery({
    queryKey: ["runs", lifecycleFilter],
    queryFn: () => listRuns(token || "", { lifecycle: lifecycleFilter || undefined }),
    enabled: !!token || isGuided(),
    refetchInterval: 10_000,
  });

  useEffect(() => {
    if (!runId && runList?.runs?.[0]) {
      setRunId(runList.runs[0].run_id);
    }
  }, [runList, runId]);

  const { data: summary, isLoading } = useQuery({
    queryKey: ["summary", runId, lens],
    queryFn: () => getRunSummary(token || "", runId!, lens === "compliance" ? undefined : lens),
    enabled: !!runId && (!!token || isGuided()),
    refetchInterval: (q) =>
      q.state.data?.status === "running" || q.state.data?.status === "queued" ? 3000 : false,
  });

  return (
    <div data-testid="run-summary-view">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-sm font-medium capitalize text-zinc-200">{lens} · run summary</h1>
        {runId ? (
          <Link
            href={`/runs/${runId}/inspector`}
            className="text-xs text-zinc-500 hover:text-zinc-300"
          >
            Inspector →
          </Link>
        ) : null}
      </div>

      <LifecycleRail active={stageRail} onSelect={setStageRail} />

      <RunSelector
        runs={runList?.runs || []}
        selectedId={runId}
        onSelect={setRunId}
        lifecycle={lifecycleFilter}
        onLifecycleChange={(v) => {
          setLifecycleFilter(v);
          if (v) setStageRail(v);
        }}
      />

      {isLoading ? (
        <div className="text-xs text-zinc-600">Loading run summary…</div>
      ) : summary ? (
        <>
          <div className="mb-4 grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
            <Meta label="Status" value={summary.status} />
            <Meta label="Model" value={summary.model_id} mono />
            <Meta label="Lifecycle" value={summary.lifecycle_stage} />
            <Meta label="Catalog" value={summary.catalog_version || "—"} mono />
          </div>

          {summary.triage_counts ? (
            <div className="mb-4 flex gap-4 text-xs text-zinc-500">
              {(["failed", "fallback", "uncovered"] as const).map((k) =>
                summary.triage_counts[k] ? (
                  <span key={k} className="capitalize">
                    {k}: <span className="text-zinc-300">{summary.triage_counts[k]}</span>
                  </span>
                ) : null,
              )}
            </div>
          ) : null}

          {summary.trust_factor ? (
            <div className="mb-4 max-w-md">
              <TrustFactorCard tf={summary.trust_factor} />
            </div>
          ) : null}

          <CoverageBar requirements={summary.requirements} />
          <ComplaiTriageTable
            requirements={summary.requirements}
            runId={summary.run_id}
            token={token}
            artifactLinks={summary.artifacts}
          />
          <HarnessProvenanceTable rows={summary.harness_provenance} />
          <NonMeasurableStrip slots={summary.non_measurable} runId={summary.run_id} />

          <div className="mt-6 border-t border-zinc-800 pt-3">
            <button
              type="button"
              onClick={() => setShowAdvanced((s) => !s)}
              className="text-xs text-zinc-500 hover:text-zinc-300"
            >
              {showAdvanced ? "▾" : "▸"} Governance & trends (MVP3)
            </button>
            {showAdvanced ? (
              <div className="mt-3 space-y-4">
                <div className="rounded border border-zinc-800 p-3">
                  <div className="mb-2 flex items-center gap-2 text-xs text-zinc-400">
                    Trend for
                    <select
                      value={trendReq}
                      onChange={(e) => setTrendReq(e.target.value)}
                      className="rounded border border-zinc-700 bg-zinc-900 px-1.5 py-0.5 text-zinc-200"
                    >
                      {summary.requirements.map((r) => (
                        <option key={r.id} value={r.id}>
                          {r.id} — {r.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <TrendCurve requirement={trendReq} modelId={summary.model_id} />
                </div>
                <HitlReviewPanel runId={summary.run_id} />
                <DeclarativeForms runId={summary.run_id} />
                <div>
                  <button
                    type="button"
                    onClick={() =>
                      downloadAuditPdf(token, summary.run_id).catch((e) => setPdfError(String(e)))
                    }
                    className="rounded border border-zinc-700 px-3 py-1 text-xs text-zinc-300 hover:bg-zinc-900"
                  >
                    ⬇ Download signed audit PDF
                  </button>
                  {pdfError ? (
                    <p className="mt-1 text-[11px] text-amber-500">
                      PDF export needs the optional &lsquo;pdf&rsquo; extra (WeasyPrint). {pdfError.slice(0, 80)}
                    </p>
                  ) : null}
                </div>
              </div>
            ) : null}
          </div>
        </>
      ) : (
        <div className="text-xs text-zinc-600">Select a run to view COMPL-AI triage.</div>
      )}
    </div>
  );
}

function Meta({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="border border-zinc-800 p-2">
      <div className="text-zinc-600">{label}</div>
      <div className={`truncate text-zinc-300 ${mono ? "font-mono" : ""}`}>{value}</div>
    </div>
  );
}
