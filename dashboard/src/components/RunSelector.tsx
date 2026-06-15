"use client";

import type { RunListItem } from "@/lib/types";

interface Props {
  runs: RunListItem[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  lifecycle: string;
  onLifecycleChange: (v: string) => void;
}

const LIFECYCLES = ["", "data", "finetune", "inference", "production"];

export function RunSelector({
  runs,
  selectedId,
  onSelect,
  lifecycle,
  onLifecycleChange,
}: Props) {
  return (
    <div className="mb-4 flex flex-wrap items-end gap-4 border border-zinc-800 bg-zinc-900/50 p-3 text-xs">
      <label className="flex flex-col gap-1">
        <span className="text-zinc-500">Lifecycle</span>
        <select
          value={lifecycle}
          onChange={(e) => onLifecycleChange(e.target.value)}
          className="rounded border border-zinc-700 bg-zinc-950 px-2 py-1 text-zinc-200"
        >
          <option value="">All stages</option>
          {LIFECYCLES.filter(Boolean).map((l) => (
            <option key={l} value={l}>
              {l}
            </option>
          ))}
        </select>
      </label>
      <label className="flex min-w-[280px] flex-1 flex-col gap-1">
        <span className="text-zinc-500">Run</span>
        <select
          value={selectedId || ""}
          onChange={(e) => onSelect(e.target.value)}
          className="rounded border border-zinc-700 bg-zinc-950 px-2 py-1 font-mono text-zinc-200"
        >
          <option value="">Select run…</option>
          {runs.map((r) => (
            <option key={r.run_id} value={r.run_id}>
              {r.run_id.slice(0, 8)} · {r.model_id} · {r.lifecycle_stage} · {r.status}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
