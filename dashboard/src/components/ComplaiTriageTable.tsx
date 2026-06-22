"use client";

import { useState } from "react";
import type { RequirementRow } from "@/lib/types";
import { RequirementDrawer } from "./RequirementDrawer";

const TRIAGE_STYLE: Record<string, string> = {
  failed: "text-status-blocked",
  fallback: "text-status-partial",
  uncovered: "text-status-partial",
  ok: "text-ink-secondary",
  na: "text-ink-secondary",
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
        <span className="text-ink-secondary">
          Requirements · {visible.length} shown
          {!showAll ? " (failed / fallback / uncovered)" : ""}
        </span>
        <label className="flex items-center gap-2 text-ink-secondary">
          <input
            type="checkbox"
            checked={showAll}
            onChange={(e) => setShowAll(e.target.checked)}
            className="rounded border-default"
          />
          Show all
        </label>
      </div>
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr className="border-b border-default text-left text-ink-secondary">
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
              className="cursor-pointer border-b border-default hover:bg-hover"
              onClick={() => setDrawer(r)}
            >
              <td className="py-1.5 pr-2 font-mono text-ink">{r.id}</td>
              <td className="py-1.5 pr-2 font-mono">
                {r.score != null ? r.score.toFixed(3) : "—"}
              </td>
              <td className="py-1.5 pr-2 font-mono text-ink-secondary">
                {r.score_ci_lower != null && r.score_ci_upper != null
                  ? `[${r.score_ci_lower.toFixed(2)}–${r.score_ci_upper.toFixed(2)}]`
                  : "—"}
              </td>
              <td className={`py-1.5 pr-2 capitalize ${TRIAGE_STYLE[r.triage]}`}>{r.triage}</td>
              <td className="max-w-md truncate py-1.5 pr-2 text-ink-secondary">{r.rationale}</td>
              <td className="py-1.5 text-ink-secondary" onClick={(e) => e.stopPropagation()}>
                <button
                  type="button"
                  className="mr-2 hover:text-ink"
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
