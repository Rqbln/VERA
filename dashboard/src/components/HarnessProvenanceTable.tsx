"use client";

import type { HarnessRow } from "@/lib/types";

export function HarnessProvenanceTable({ rows }: { rows: HarnessRow[] }) {
  if (!rows.length) return null;
  return (
    <div className="mt-4">
      <div className="mb-1 text-xs text-ink-secondary">Harness provenance</div>
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-default text-left text-ink-secondary">
            <th className="py-1 pr-2">Benchmark</th>
            <th className="py-1 pr-2">Harness</th>
            <th className="py-1 pr-2">Agent</th>
            <th className="py-1">Fallback</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.benchmark_id} className="border-b border-default">
              <td className="py-1 pr-2 font-mono">{r.benchmark_id}</td>
              <td className="py-1 pr-2">{r.harness}</td>
              <td className="py-1 pr-2">{r.agent}</td>
              <td className={`py-1 ${r.fallback === "yes" || r.fallback === true ? "text-status-partial" : "text-ink-secondary"}`}>
                {String(r.fallback)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
