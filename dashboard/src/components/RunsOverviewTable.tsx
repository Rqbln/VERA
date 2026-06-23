"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { listRuns } from "@/lib/api";
import { getToken, isGuided } from "@/lib/auth";
import type { RunListItem } from "@/lib/types";

const STATUS_COLOR: Record<string, string> = {
  completed: "bg-status-ok/10 text-status-ok",
  running: "bg-status-info/10 text-status-info",
  queued: "bg-surface-2 text-ink-secondary",
  failed: "bg-status-blocked/10 text-status-blocked",
};

export function RunsOverviewTable() {
  const token = getToken();
  const { data, isLoading } = useQuery({
    queryKey: ["runs-overview"],
    queryFn: () => listRuns(token || "", { includeTriage: true }),
    enabled: !!token || isGuided(),
    refetchInterval: (q) => {
      const runs = q.state.data?.runs ?? [];
      return runs.some((r) => r.status === "running" || r.status === "queued") ? 5000 : 20000;
    },
  });

  const runs = data?.runs ?? [];
  const counts = {
    queued: runs.filter((r) => r.status === "queued").length,
    running: runs.filter((r) => r.status === "running").length,
    completed: runs.filter((r) => r.status === "completed").length,
    failed: runs.filter((r) => r.status === "failed").length,
  };

  return (
    <div data-testid="runs-overview">
      <div className="mb-3 flex items-center justify-between">
        <h1 className="text-sm font-medium text-ink">Runs</h1>
        <Link
          href="/launch"
          className="rounded bg-brand px-3 py-1 text-xs font-medium text-white hover:bg-brand-deep"
        >
          + Launch evaluation
        </Link>
      </div>

      <div className="mb-3 flex gap-3 text-xs text-ink-secondary">
        <span>queued <span className="text-ink">{counts.queued}</span></span>
        <span>running <span className="text-status-info">{counts.running}</span></span>
        <span>completed <span className="text-status-ok">{counts.completed}</span></span>
        <span>failed <span className="text-status-blocked">{counts.failed}</span></span>
      </div>

      {isLoading ? (
        <p className="text-xs text-ink-secondary">Loading runs…</p>
      ) : runs.length === 0 ? (
        <div className="rounded border border-default p-4 text-xs text-ink-secondary">
          No runs yet. <Link href="/launch" className="text-status-ok">Launch your first evaluation →</Link>
        </div>
      ) : (
        <table className="w-full text-[13px]">
          <thead>
            <tr className="border-b border-default text-left text-[11px] uppercase tracking-wide text-ink-secondary">
              <th className="py-1.5 pr-2 font-medium">Run</th>
              <th className="py-1.5 pr-2 font-medium">Model</th>
              <th className="py-1.5 pr-2 font-medium">Lifecycle</th>
              <th className="py-1.5 pr-2 font-medium">Status</th>
              <th className="py-1.5 pr-2 font-medium">Triage</th>
              <th className="py-1.5 pr-2 font-medium">Score</th>
              <th className="py-1.5 pr-2 font-medium">Created</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((r) => (
              <Row key={r.run_id} r={r} />
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function Row({ r }: { r: RunListItem }) {
  const tc = r.triage_counts;
  return (
    <tr className="border-b border-default hover:bg-hover">
      <td className="py-1.5 pr-2">
        <Link href={`/runs/${r.run_id}`} className="font-mono text-ink hover:text-ink">
          {r.run_id.slice(0, 8)}
        </Link>
      </td>
      <td className="py-1.5 pr-2 font-mono text-ink-secondary">{r.model_id.replace("ollama/", "")}</td>
      <td className="py-1.5 pr-2 text-ink-secondary">{r.lifecycle_stage}</td>
      <td className="py-1.5 pr-2">
        <span className={`rounded px-1.5 py-0.5 text-[11px] ${STATUS_COLOR[r.status] || "bg-surface-2 text-ink-secondary"}`}>
          {r.status}
        </span>
      </td>
      <td className="py-1.5 pr-2 text-xs">
        {tc ? (
          <span className="flex gap-2">
            {tc.failed ? <span className="text-status-blocked">{tc.failed} failed</span> : null}
            {tc.fallback ? <span className="text-status-partial">{tc.fallback} fallback</span> : null}
            {tc.uncovered ? <span className="text-ink-secondary">{tc.uncovered} uncov.</span> : null}
            {!tc.failed && !tc.fallback && !tc.uncovered ? (
              <span className="text-status-ok">clean</span>
            ) : null}
          </span>
        ) : (
          <span className="text-ink-secondary">—</span>
        )}
      </td>
      <td className="py-1.5 pr-2 font-mono text-ink">
        {r.headline_score != null ? r.headline_score.toFixed(2) : "—"}
      </td>
      <td className="py-1.5 pr-2 text-ink-secondary">{r.created_at?.slice(0, 16).replace("T", " ")}</td>
    </tr>
  );
}
