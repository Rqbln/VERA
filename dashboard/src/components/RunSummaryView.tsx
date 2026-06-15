"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { listRuns, getRunSummary } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { RunSelector } from "./RunSelector";
import { LifecycleRail } from "./LifecycleRail";
import { CoverageBar } from "./CoverageBar";
import { ComplaiTriageTable } from "./ComplaiTriageTable";
import { NonMeasurableStrip } from "./NonMeasurableStrip";
import { HarnessProvenanceTable } from "./HarnessProvenanceTable";
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

  const { data: runList } = useQuery({
    queryKey: ["runs", lifecycleFilter],
    queryFn: () => listRuns(token || "", { lifecycle: lifecycleFilter || undefined }),
    enabled: !!token || process.env.NEXT_PUBLIC_AUTH_DISABLED === "1",
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
    enabled: !!runId && (!!token || process.env.NEXT_PUBLIC_AUTH_DISABLED === "1"),
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

          <CoverageBar requirements={summary.requirements} />
          <ComplaiTriageTable
            requirements={summary.requirements}
            runId={summary.run_id}
            token={token}
            artifactLinks={summary.artifacts}
          />
          <HarnessProvenanceTable rows={summary.harness_provenance} />
          <NonMeasurableStrip slots={summary.non_measurable} runId={summary.run_id} />
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
