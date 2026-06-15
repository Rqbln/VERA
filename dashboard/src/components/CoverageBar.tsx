"use client";

import type { RequirementRow } from "@/lib/types";

const BAND_COLOR: Record<string, string> = {
  green: "#059669",
  orange: "#d97706",
  red: "#dc2626",
  unknown: "#52525b",
};

interface Props {
  requirements: RequirementRow[];
}

export function CoverageBar({ requirements }: Props) {
  if (!requirements.length) return null;

  return (
    <div className="mb-4">
      <div className="mb-1 text-xs text-zinc-500">COMPL-AI coverage</div>
      <div className="flex h-6 overflow-hidden rounded border border-zinc-800">
        {requirements.map((r) => (
          <div
            key={r.id}
            title={`${r.id}: ${r.score?.toFixed(2) ?? "—"} [${r.score_ci_lower?.toFixed(2) ?? "—"}–${r.score_ci_upper?.toFixed(2) ?? "—"}]`}
            className="flex-1 border-r border-zinc-900 last:border-r-0"
            style={{ backgroundColor: BAND_COLOR[r.band] || BAND_COLOR.unknown }}
          />
        ))}
      </div>
      <div className="mt-1 flex justify-between font-mono text-[10px] text-zinc-600">
        <span>R01</span>
        <span>R12</span>
      </div>
    </div>
  );
}
