"use client";

import type { LucideIcon } from "lucide-react";

export interface Kpi {
  label: string;
  value: string | number;
  icon?: LucideIcon;
  accent?: string; // small accent line under the value, in vivid green
  tone?: "ok" | "partial" | "blocked" | "neutral";
}

const TONE: Record<string, string> = {
  ok: "text-status-ok",
  partial: "text-status-partial",
  blocked: "text-status-blocked",
  neutral: "text-ink",
};

export function KpiTile({ kpi }: { kpi: Kpi }) {
  const Icon = kpi.icon;
  return (
    <div className="kpi-tile">
      <div className="flex items-center justify-between">
        <span className="kpi-label">{kpi.label}</span>
        {Icon ? <Icon size={16} strokeWidth={1.75} className="text-brand-accent" /> : null}
      </div>
      <span className={`kpi-value ${TONE[kpi.tone ?? "neutral"]}`}>{kpi.value}</span>
      {kpi.accent ? (
        <span className="flex items-center gap-1 text-[11px] text-brand-accent">
          <span className="h-0.5 w-4 rounded-full bg-brand-accent" />
          {kpi.accent}
        </span>
      ) : null}
    </div>
  );
}

export function KpiRow({ kpis }: { kpis: Kpi[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {kpis.map((k) => (
        <KpiTile key={k.label} kpi={k} />
      ))}
    </div>
  );
}
