"use client";

import { useQuery } from "@tanstack/react-query";
import { getRawOutputs, presignArtifact } from "@/lib/api";
import type { RequirementRow } from "@/lib/types";

interface Props {
  row: RequirementRow;
  runId: string;
  token: string | undefined;
  artifactLinks?: Record<string, string>;
  onClose: () => void;
}

export function RequirementDrawer({ row, runId, token, onClose }: Props) {
  const benchmark = row.contributing_benchmarks[0];
  const { data: raw } = useQuery({
    queryKey: ["raw-outputs", runId, benchmark],
    queryFn: () => getRawOutputs(token || "", runId, benchmark || ""),
    enabled: !!benchmark && !!token,
  });

  async function openArtifact(kind: string) {
    if (!token) return;
    try {
      const { url } = await presignArtifact(token, runId, kind);
      window.open(url, "_blank");
    } catch {
      /* presign may fail without MinIO */
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/50" onClick={onClose}>
      <div
        className="h-full w-full max-w-lg overflow-y-auto border-l border-default bg-white p-4 text-xs"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h2 className="font-mono text-sm text-ink">
              {row.id} · {row.name}
            </h2>
            <p className="mt-1 text-ink-secondary">{row.rationale}</p>
          </div>
          <button type="button" onClick={onClose} className="text-ink-secondary hover:text-ink">
            ✕
          </button>
        </div>
        <dl className="mb-4 grid grid-cols-2 gap-2 text-ink-secondary">
          <dt>Score</dt>
          <dd className="font-mono text-ink">
            {row.score?.toFixed(4) ?? "—"} · band {row.band}
          </dd>
          <dt>CI 95%</dt>
          <dd className="font-mono">
            [{row.score_ci_lower?.toFixed(4) ?? "—"}, {row.score_ci_upper?.toFixed(4) ?? "—"}]
          </dd>
          <dt>EU AI Act</dt>
          <dd>{row.aiact}</dd>
          <dt>Triage</dt>
          <dd className="capitalize">{row.triage}</dd>
        </dl>
        <div className="mb-4">
          <div className="mb-1 text-ink-secondary">Contributing benchmarks</div>
          <ul className="font-mono text-ink-secondary">
            {row.contributing_benchmarks.map((b) => (
              <li key={b}>
                {b}
                {row.fallback_benchmarks.includes(b) ? (
                  <span className="ml-2 text-status-partial">fallback</span>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
        <div className="mb-4 flex gap-2">
          <button
            type="button"
            onClick={() => openArtifact("benchmark_run")}
            className="rounded border border-default px-2 py-1 text-ink-secondary hover:bg-hover"
          >
            benchmark_run.yaml
          </button>
          <button
            type="button"
            onClick={() => openArtifact("model_card")}
            className="rounded border border-default px-2 py-1 text-ink-secondary hover:bg-hover"
          >
            model card
          </button>
          <button
            type="button"
            onClick={() => openArtifact("raw_outputs")}
            className="rounded border border-default px-2 py-1 text-ink-secondary hover:bg-hover"
          >
            raw_outputs.jsonl
          </button>
        </div>
        {raw?.rows?.length ? (
          <div>
            <div className="mb-1 text-ink-secondary">Raw outputs (sample)</div>
            <pre className="max-h-64 overflow-auto rounded border border-default bg-surface-2 p-2 font-mono text-[10px] text-ink-secondary">
              {JSON.stringify(raw.rows.slice(0, 3), null, 2)}
            </pre>
          </div>
        ) : null}
      </div>
    </div>
  );
}
