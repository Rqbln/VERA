"use client";

import { useState } from "react";
import type { RequirementRow } from "@/lib/types";
import { RequirementDrawer } from "./RequirementDrawer";

const TRIAGE_STYLE: Record<string, string> = {
  failed: "text-red-400",
  fallback: "text-amber-400",
  uncovered: "text-orange-400",
  ok: "text-zinc-400",
  na: "text-zinc-600",
};

interface Props {
  requirements: RequirementRow[];
  runId: string;
  token: string | undefined;
  artifactLinks?: Record<string, string>;
}

export function ComplaiTriageTable({ requirements, runId, token, artifactLinks }: Props) {
  const [showAll, setShowAll] = useState(false);
  const [drawer, setDrawer] = useState<RequirementRow | null>(null);

  const visible = showAll
    ? requirements
    : requirements.filter((r) => !["ok", "na"].includes(r.triage));

  return (
    <>
      <div className="mb-2 flex items-center justify-between text-xs">
        <span className="text-zinc-500">
          Requirements · {visible.length} shown
          {!showAll ? " (failed / fallback / uncovered)" : ""}
        </span>
        <label className="flex items-center gap-2 text-zinc-500">
          <input
            type="checkbox"
            checked={showAll}
            onChange={(e) => setShowAll(e.target.checked)}
            className="rounded border-zinc-700"
          />
          Show all
        </label>
      </div>
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr className="border-b border-zinc-800 text-left text-zinc-500">
            <th className="py-1.5 pr-2 font-medium">ID</th>
            <th className="py-1.5 pr-2 font-medium">Score</th>
            <th className="py-1.5 pr-2 font-medium">CI 95%</th>
            <th className="py-1.5 pr-2 font-medium">Status</th>
            <th className="py-1.5 pr-2 font-medium">Rationale</th>
            <th className="py-1.5 font-medium">Links</th>
          </tr>
        </thead>
        <tbody>
          {visible.map((r) => (
            <tr
              key={r.id}
              className="cursor-pointer border-b border-zinc-900 hover:bg-zinc-900/60"
              onClick={() => setDrawer(r)}
            >
              <td className="py-1.5 pr-2 font-mono text-zinc-300">{r.id}</td>
              <td className="py-1.5 pr-2 font-mono">
                {r.score != null ? r.score.toFixed(3) : "—"}
              </td>
              <td className="py-1.5 pr-2 font-mono text-zinc-500">
                {r.score_ci_lower != null && r.score_ci_upper != null
                  ? `[${r.score_ci_lower.toFixed(2)}–${r.score_ci_upper.toFixed(2)}]`
                  : "—"}
              </td>
              <td className={`py-1.5 pr-2 capitalize ${TRIAGE_STYLE[r.triage]}`}>{r.triage}</td>
              <td className="max-w-md truncate py-1.5 pr-2 text-zinc-500">{r.rationale}</td>
              <td className="py-1.5 text-zinc-600" onClick={(e) => e.stopPropagation()}>
                <button
                  type="button"
                  className="mr-2 hover:text-zinc-300"
                  onClick={() => setDrawer(r)}
                >
                  drill-down
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {drawer ? (
        <RequirementDrawer
          row={drawer}
          runId={runId}
          token={token}
          artifactLinks={artifactLinks}
          onClose={() => setDrawer(null)}
        />
      ) : null}
    </>
  );
}
