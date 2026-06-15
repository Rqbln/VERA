"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { listRuns } from "@/lib/api";
import { getToken, isGuided } from "@/lib/auth";
import type { RunListItem } from "@/lib/types";

const STATUS_COLOR: Record<string, string> = {
  completed: "bg-emerald-900/40 text-emerald-400",
  running: "bg-blue-900/40 text-blue-300",
  queued: "bg-zinc-800 text-zinc-400",
  failed: "bg-red-900/40 text-red-400",
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
        <h1 className="text-sm font-medium text-zinc-200">Runs</h1>
        <Link
          href="/launch"
          className="rounded bg-zinc-100 px-3 py-1 text-xs font-medium text-zinc-900 hover:bg-white"
        >
          + Launch evaluation
        </Link>
      </div>

      <div className="mb-3 flex gap-3 text-xs text-zinc-500">
        <span>queued <span className="text-zinc-300">{counts.queued}</span></span>
        <span>running <span className="text-blue-300">{counts.running}</span></span>
        <span>completed <span className="text-emerald-400">{counts.completed}</span></span>
        <span>failed <span className="text-red-400">{counts.failed}</span></span>
      </div>

      {isLoading ? (
        <p className="text-xs text-zinc-600">Loading runs…</p>
      ) : runs.length === 0 ? (
        <div className="rounded border border-zinc-800 p-4 text-xs text-zinc-500">
          No runs yet. <Link href="/launch" className="text-emerald-500">Launch your first evaluation →</Link>
        </div>
      ) : (
        <table className="w-full text-[13px]">
          <thead>
            <tr className="border-b border-zinc-800 text-left text-[11px] uppercase tracking-wide text-zinc-600">
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
    <tr className="border-b border-zinc-900 hover:bg-zinc-900/40">
      <td className="py-1.5 pr-2">
        <Link href={`/runs/${r.run_id}`} className="font-mono text-zinc-300 hover:text-zinc-100">
          {r.run_id.slice(0, 8)}
        </Link>
      </td>
      <td className="py-1.5 pr-2 font-mono text-zinc-400">{r.model_id.replace("ollama/", "")}</td>
      <td className="py-1.5 pr-2 text-zinc-400">{r.lifecycle_stage}</td>
      <td className="py-1.5 pr-2">
        <span className={`rounded px-1.5 py-0.5 text-[11px] ${STATUS_COLOR[r.status] || "bg-zinc-800 text-zinc-400"}`}>
          {r.status}
        </span>
      </td>
      <td className="py-1.5 pr-2 text-xs">
        {tc ? (
          <span className="flex gap-2">
            {tc.failed ? <span className="text-red-400">{tc.failed} failed</span> : null}
            {tc.fallback ? <span className="text-amber-400">{tc.fallback} fallback</span> : null}
            {tc.uncovered ? <span className="text-zinc-500">{tc.uncovered} uncov.</span> : null}
            {!tc.failed && !tc.fallback && !tc.uncovered ? (
              <span className="text-emerald-500">clean</span>
            ) : null}
          </span>
        ) : (
          <span className="text-zinc-700">—</span>
        )}
      </td>
      <td className="py-1.5 pr-2 font-mono text-zinc-300">
        {r.headline_score != null ? r.headline_score.toFixed(2) : "—"}
      </td>
      <td className="py-1.5 pr-2 text-zinc-600">{r.created_at?.slice(0, 16).replace("T", " ")}</td>
    </tr>
  );
}
