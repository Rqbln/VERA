"use client";

import type { RequirementRow } from "@/lib/types";
import { useT } from "@/lib/i18n";

export const BAND_COLOR: Record<string, string> = {
  green: "#00915a",
  orange: "#e8a33d",
  red: "#c0392b",
  unknown: "#cfd6d2",
};

interface Props {
  requirements: RequirementRow[];
}

export function CoverageBar({ requirements }: Props) {
  const t = useT();
  if (!requirements.length) return null;

  return (
    <div className="mb-4">
      <div className="mb-1 text-xs text-ink-secondary">{t("summary.coverage")}</div>
      <div className="flex h-5 overflow-hidden rounded-md border border-default">
        {requirements.map((r) => (
          <div
            key={r.id}
            title={`${r.id}: ${r.score?.toFixed(2) ?? "—"} [${r.score_ci_lower?.toFixed(2) ?? "—"}–${r.score_ci_upper?.toFixed(2) ?? "—"}]`}
            className="flex-1 border-r border-default last:border-r-0"
            style={{ backgroundColor: BAND_COLOR[r.band] || BAND_COLOR.unknown }}
          />
        ))}
      </div>
      <div className="mt-1 flex justify-between font-mono text-[10px] text-ink-secondary">
        <span>R01</span>
        <span>R12</span>
      </div>
    </div>
  );
}
